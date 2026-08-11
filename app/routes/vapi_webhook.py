"""
Vapi Webhook Handler

Vapi sends POST requests to our server URL when the voice agent triggers
a tool/function call. We handle two tools:

1. save_patient — Persists patient data to the database after caller confirms.
2. check_existing_patient — Checks if a patient with given phone number already exists.

Webhook payload format (function-call):
{
    "message": {
        "type": "function-call",
        "functionCall": {
            "name": "savePatient",
            "parameters": { ... patient fields ... }
        },
        "call": { ... call metadata ... }
    }
}

Response format:
{
    "result": "Success message or error description"
}
"""

import logging
import re
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import PatientCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vapi", tags=["vapi"])


def _clean_phone(phone: str) -> str:
    """Extract 10-digit US phone number from various formats."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def _parse_date(date_str: str) -> date:
    """Parse date from various formats the LLM might produce."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return date.fromisoformat(date_str) if fmt == "%Y-%m-%d" else __import__("datetime").datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


@router.post("/webhook")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    """Main Vapi webhook endpoint. Routes to appropriate handler based on message type."""
    body = await request.json()
    message = body.get("message", {})
    msg_type = message.get("type", "")

    logger.info(f"Vapi webhook received: type={msg_type}")

    if msg_type == "function-call":
        fn_call = message.get("functionCall", {})
        fn_name = fn_call.get("name", "")
        params = fn_call.get("parameters", {})

        logger.info(f"Function call: {fn_name} with params: {params}")

        if fn_name == "savePatient":
            return _handle_save_patient(params, db)
        elif fn_name == "checkExistingPatient":
            return _handle_check_existing(params, db)
        else:
            return {"result": f"Unknown function: {fn_name}"}

    elif msg_type == "assistant-request":
        # Could dynamically configure assistant here; return empty to use defaults
        return {}

    elif msg_type == "end-of-call-report":
        # Log call summary
        summary = message.get("summary", "No summary")
        call_id = message.get("call", {}).get("id", "unknown")
        logger.info(f"Call ended [{call_id}]: {summary}")
        return {}

    elif msg_type == "status-update":
        status = message.get("status", "unknown")
        logger.info(f"Call status update: {status}")
        return {}

    # Default: acknowledge unknown message types
    return {}


def _handle_save_patient(params: dict, db: Session) -> dict:
    """Save patient record from voice agent collected data."""
    try:
        # Normalize phone number
        if "phone_number" in params:
            params["phone_number"] = _clean_phone(params["phone_number"])

        # Parse date of birth
        if "date_of_birth" in params:
            params["date_of_birth"] = _parse_date(str(params["date_of_birth"]))

        # Normalize state to uppercase
        if "state" in params:
            params["state"] = params["state"].upper().strip()

        # Normalize sex field
        sex_map = {
            "male": "Male",
            "female": "Female",
            "other": "Other",
            "decline": "Decline to Answer",
            "decline to answer": "Decline to Answer",
            "prefer not to say": "Decline to Answer",
        }
        if "sex" in params:
            params["sex"] = sex_map.get(params["sex"].lower(), params["sex"])

        # Clean emergency contact phone if provided
        if params.get("emergency_contact_phone"):
            params["emergency_contact_phone"] = _clean_phone(params["emergency_contact_phone"])

        # Validate via Pydantic schema
        patient_data = PatientCreate(**params)
        patient = Patient(**patient_data.model_dump())

        db.add(patient)
        db.commit()
        db.refresh(patient)

        logger.info(
            f"Patient saved via voice: {patient.patient_id} — "
            f"{patient.first_name} {patient.last_name}"
        )

        return {
            "result": (
                f"Patient registered successfully. "
                f"Patient ID is {patient.patient_id}. "
                f"Name: {patient.first_name} {patient.last_name}."
            )
        }

    except ValueError as e:
        logger.warning(f"Validation error saving patient: {e}")
        return {"result": f"Could not save patient. Validation error: {str(e)}"}
    except Exception as e:
        db.rollback()
        logger.error(f"Database error saving patient: {e}")
        return {"result": "Sorry, there was a system error saving the patient record. Please try again."}


def _handle_check_existing(params: dict, db: Session) -> dict:
    """Check if patient exists by phone number (for duplicate detection)."""
    phone = params.get("phone_number", "")
    if not phone:
        return {"result": "No phone number provided to check."}

    digits = _clean_phone(phone)

    patient = (
        db.query(Patient)
        .filter(Patient.phone_number == digits, Patient.deleted_at.is_(None))
        .first()
    )

    if patient:
        return {
            "result": (
                f"Existing patient found: {patient.first_name} {patient.last_name}, "
                f"Patient ID: {patient.patient_id}. "
                f"Ask the caller if they want to update their existing record."
            )
        }
    else:
        return {"result": "No existing patient found with that phone number. Proceed with new registration."}

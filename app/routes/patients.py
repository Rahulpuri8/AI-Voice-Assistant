import logging
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import (
    APIResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=APIResponse)
def list_patients(
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[date] = Query(None),
    phone_number: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all patients with optional filters. Excludes soft-deleted records."""
    query = db.query(Patient).filter(Patient.deleted_at.is_(None))

    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name}%"))
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)
    if phone_number:
        # Strip non-digits for flexible matching
        import re
        digits = re.sub(r"\D", "", phone_number)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        query = query.filter(Patient.phone_number == digits)

    patients = query.order_by(Patient.created_at.desc()).all()
    return APIResponse(
        data=[PatientResponse.model_validate(p).model_dump(mode="json") for p in patients]
    )


@router.get("/{patient_id}", response_model=APIResponse)
def get_patient(patient_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single patient by UUID."""
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return APIResponse(
        data=PatientResponse.model_validate(patient).model_dump(mode="json")
    )


@router.post("", response_model=APIResponse, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient record."""
    patient = Patient(**payload.model_dump())
    db.add(patient)
    try:
        db.commit()
        db.refresh(patient)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create patient: {e}")
        raise HTTPException(status_code=500, detail="Failed to save patient record")

    logger.info(f"Patient created: {patient.patient_id} — {patient.first_name} {patient.last_name}")
    return APIResponse(
        data=PatientResponse.model_validate(patient).model_dump(mode="json")
    )


@router.put("/{patient_id}", response_model=APIResponse)
def update_patient(patient_id: UUID, payload: PatientUpdate, db: Session = Depends(get_db)):
    """Update an existing patient. Partial updates allowed."""
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=422, detail="No fields provided for update")

    for field, value in update_data.items():
        setattr(patient, field, value)

    patient.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(patient)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update patient record")

    logger.info(f"Patient updated: {patient_id}")
    return APIResponse(
        data=PatientResponse.model_validate(patient).model_dump(mode="json")
    )


@router.delete("/{patient_id}", response_model=APIResponse)
def delete_patient(patient_id: UUID, db: Session = Depends(get_db)):
    """Soft-delete a patient by setting deleted_at timestamp."""
    patient = (
        db.query(Patient)
        .filter(Patient.patient_id == patient_id, Patient.deleted_at.is_(None))
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.deleted_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete patient record")

    logger.info(f"Patient soft-deleted: {patient_id}")
    return APIResponse(data={"message": f"Patient {patient_id} deleted successfully"})

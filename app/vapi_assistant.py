"""
Vapi Assistant Configuration

This module defines the assistant configuration and tools that will be
registered with Vapi. Run `python -m app.vapi_assistant` to create/update
the assistant via Vapi API.

The system prompt is carefully engineered for natural, warm patient intake
conversation while ensuring all required fields are collected and validated.
"""

import json
import httpx
from app.config import settings

# ============================================================================
# SYSTEM PROMPT — Core of the voice agent's personality and behavior
# ============================================================================

SYSTEM_PROMPT = """You are a friendly, professional patient intake coordinator named Sarah at a healthcare clinic. Your job is to collect patient registration information through natural, warm conversation.

## Personality
- Warm, patient, and reassuring — like a caring receptionist
- Speak naturally, not robotically. Use contractions ("I'll", "we'll", "let's")
- Be concise — phone conversations should not feel long
- If the caller seems confused or nervous, reassure them

## Conversation Flow

### 1. Greeting
Start with: "Hi there! Thank you for calling. I'm Sarah, and I'll be helping you get registered as a new patient today. This will only take a few minutes. Let's start with your name — what's your first and last name?"

### 2. Collect Required Fields (in this natural order)
Collect these one or two at a time. Don't dump all questions at once.

- **Full name** (first_name, last_name)
- **Date of birth** — Ask: "And what's your date of birth?" Accept natural formats like "March 15th, 1990" or "3/15/1990"
- **Sex** — Ask sensitively: "For our medical records, how would you like us to record your sex? We have Male, Female, Other, or you can decline to answer."
- **Phone number** — Ask: "What's the best phone number to reach you at?" (You may already have this from caller ID — confirm it)
- **Address** — Ask: "What's your home address?" Listen for street, city, state, and zip in one natural response. If they give partial info, ask for the missing parts.

### 3. Optional Fields
After collecting all required fields, offer optional ones:
"Great, I have all the essential information. I can also note down your insurance details, an emergency contact, email address, and preferred language if you'd like to provide any of those. Would you like to add any of that?"

If yes, collect what they offer. If no, move to confirmation.

### 4. Confirmation (CRITICAL — never skip this)
Read back ALL collected information clearly:
"Alright, let me read everything back to make sure I have it right:
- Name: [first] [last]
- Date of birth: [DOB]
- Sex: [sex]
- Phone: [phone]
- Address: [full address]
[any optional fields they provided]

Does everything sound correct, or would you like to change anything?"

### 5. Handle Corrections
If they want to correct something:
- Listen carefully to the correction
- Repeat the corrected value back
- Ask if there's anything else to fix

### 6. Save and Close
After confirmation, call the savePatient function with all collected data.
Then say: "You're all set, [First Name]! Your registration is complete. Is there anything else I can help you with today?"

If they say no: "Have a wonderful day! Goodbye."

## Validation Rules (re-prompt if invalid)
- **Names**: Must be alphabetic (hyphens and apostrophes OK). If unclear spelling, ask them to spell it out.
- **Date of birth**: Must be a real date, not in the future. If ambiguous, confirm: "Just to confirm, that's [month] [day], [year]?"
- **Phone number**: Must be 10 digits. If they give fewer, say: "I think I might be missing a digit — could you repeat that?"
- **State**: Must be a valid US state. If they say the full name, convert to abbreviation.
- **Zip code**: Must be 5 digits (or ZIP+4 format).

## Handling Edge Cases
- **Caller wants to start over**: "No problem at all! Let's start fresh. What's your first and last name?"
- **Caller is unsure about a field**: Mark optional fields as null; for required fields, gently explain why you need it.
- **Caller speaks a name with unusual spelling**: Always ask them to spell it: "Could you spell that for me?"
- **Caller gives info out of order**: Accept it gracefully and track what you still need.
- **Caller interrupts**: Let them speak, acknowledge what they said, and continue naturally.

## Important Rules
- ALWAYS confirm before saving. Never skip confirmation.
- NEVER make up or assume information. If unclear, ask again.
- Keep the conversation moving — don't over-explain.
- If there's an error saving, tell the caller: "I'm sorry, I'm having a technical issue saving your information. Let me try again." Then retry the save.
- After collecting the phone number, call checkExistingPatient to check for duplicates before continuing.
"""

# ============================================================================
# TOOL DEFINITIONS — Functions the voice agent can call
# ============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "savePatient",
            "description": "Save a new patient registration to the database. Call this ONLY after the caller has confirmed all their information is correct.",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Patient's first name (alphabetic, hyphens and apostrophes allowed)"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Patient's last name"
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Date of birth in MM/DD/YYYY format"
                    },
                    "sex": {
                        "type": "string",
                        "enum": ["Male", "Female", "Other", "Decline to Answer"],
                        "description": "Patient's sex for medical records"
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "10-digit US phone number"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address (optional)"
                    },
                    "address_line_1": {
                        "type": "string",
                        "description": "Street address"
                    },
                    "address_line_2": {
                        "type": "string",
                        "description": "Apartment, suite, or unit number (optional)"
                    },
                    "city": {
                        "type": "string",
                        "description": "City name"
                    },
                    "state": {
                        "type": "string",
                        "description": "2-letter US state abbreviation (e.g., CA, NY, TX)"
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "5-digit or ZIP+4 format US zip code"
                    },
                    "insurance_provider": {
                        "type": "string",
                        "description": "Name of insurance company (optional)"
                    },
                    "insurance_member_id": {
                        "type": "string",
                        "description": "Insurance member/subscriber ID (optional)"
                    },
                    "preferred_language": {
                        "type": "string",
                        "description": "Preferred language, defaults to English (optional)"
                    },
                    "emergency_contact_name": {
                        "type": "string",
                        "description": "Emergency contact full name (optional)"
                    },
                    "emergency_contact_phone": {
                        "type": "string",
                        "description": "Emergency contact 10-digit US phone number (optional)"
                    }
                },
                "required": [
                    "first_name", "last_name", "date_of_birth", "sex",
                    "phone_number", "address_line_1", "city", "state", "zip_code"
                ]
            }
        },
        "server": {
            "url": "{server_url}/vapi/webhook"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "checkExistingPatient",
            "description": "Check if a patient already exists by phone number. Call this after collecting the caller's phone number to detect returning patients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The phone number to check"
                    }
                },
                "required": ["phone_number"]
            }
        },
        "server": {
            "url": "{server_url}/vapi/webhook"
        }
    }
]


def get_assistant_config() -> dict:
    """Return the full Vapi assistant configuration."""
    # Replace server URL placeholder in tools
    tools = json.loads(
        json.dumps(TOOLS).replace("{server_url}", settings.SERVER_URL)
    )

    return {
        "name": "Patient Registration Agent",
        "model": {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ],
            "temperature": 0.7,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "sarah",  # ElevenLabs 'Sarah' voice — warm, professional
        },
        "firstMessage": "Hi there! Thank you for calling. I'm Sarah, and I'll be helping you get registered as a new patient today. This will only take a few minutes. Let's start with your name — what's your first and last name?",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        "serverUrl": f"{settings.SERVER_URL}/vapi/webhook",
        "tools": tools,
        "endCallFunctionEnabled": True,
        "endCallMessage": "Thank you for registering with us. Have a wonderful day! Goodbye.",
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,  # 10 minute max call
        "backgroundSound": "office",
        "hipaaEnabled": False,
    }


async def create_or_update_assistant() -> dict:
    """Create the assistant in Vapi. Returns the assistant object."""
    config = get_assistant_config()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vapi.ai/assistant",
            json=config,
            headers={
                "Authorization": f"Bearer {settings.VAPI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        assistant = response.json()
        print(f"Assistant created: {assistant.get('id')}")
        print(f"Name: {assistant.get('name')}")
        return assistant


async def assign_phone_number(assistant_id: str) -> dict:
    """Assign the Vapi phone number to the assistant."""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.vapi.ai/phone-number/{settings.VAPI_PHONE_NUMBER_ID}",
            json={"assistantId": assistant_id},
            headers={
                "Authorization": f"Bearer {settings.VAPI_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        print(f"Phone number assigned to assistant {assistant_id}")
        return result


if __name__ == "__main__":
    import asyncio

    async def main():
        print("Creating Vapi assistant...")
        assistant = await create_or_update_assistant()
        assistant_id = assistant.get("id")

        if settings.VAPI_PHONE_NUMBER_ID:
            print(f"Assigning phone number {settings.VAPI_PHONE_NUMBER_ID}...")
            await assign_phone_number(assistant_id)
            print("Done! Your voice agent is ready to receive calls.")
        else:
            print(
                f"Assistant created (ID: {assistant_id}). "
                "Set VAPI_PHONE_NUMBER_ID in .env and re-run to assign a phone number."
            )

    asyncio.run(main())

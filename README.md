# Voice AI Agent — Patient Registration System

A voice-based AI agent accessible via a real phone number that collects U.S. patient demographic information through natural conversation, persists data to PostgreSQL, and exposes it through a REST API.

## Live Demo

- **Phone Number:** `+1 (864) 606-0053`
- **API Base URL:** `https://web-production-ffd29.up.railway.app`
- **API Docs:** `https://web-production-ffd29.up.railway.app/docs`

## Architecture

```
┌─────────────┐      ┌─────────────────────────────┐      ┌──────────────┐
│  Phone Call  │◄────►│  Vapi (Telephony + STT/TTS) │◄────►│   Groq LLM   │
│   (Caller)   │      │  - Deepgram Nova-2 (STT)    │      │ Llama 3.3 70B│
└─────────────┘      │  - ElevenLabs (TTS)          │      └──────────────┘
                     └──────────┬────────────────────┘
                                │ Webhooks (function calls)
                                ▼
                     ┌─────────────────────────────┐
                     │  FastAPI Backend (Python)    │
                     │  - Patient CRUD API          │
                     │  - Vapi webhook handler      │
                     │  - Input validation          │
                     └──────────┬────────────────────┘
                                │
                                ▼
                     ┌─────────────────────────────┐
                     │  PostgreSQL Database         │
                     │  (Railway managed)           │
                     └─────────────────────────────┘
```

### Component Responsibilities

| Component | Role |
|-----------|------|
| **Vapi** | Telephony, speech-to-text (Deepgram), text-to-speech (ElevenLabs), call orchestration |
| **Groq + Llama 3.3 70B** | LLM for natural conversation, field extraction, validation logic |
| **FastAPI** | REST API, webhook handler, server-side validation, database operations |
| **PostgreSQL** | Persistent patient record storage with proper schema constraints |

## Tech Stack Justification

- **Vapi**: Abstracts telephony/STT/TTS complexity. Native Groq integration. Fastest path to working voice agent.
- **Groq + Llama 3.3 70B**: Free tier, ultra-low latency (~100ms inference). Critical for natural voice conversation — users expect near-instant responses.
- **FastAPI**: Async Python, auto-generated OpenAPI docs, Pydantic validation built-in. Ideal for API-first backend.
- **PostgreSQL**: Production-grade relational DB. Proper constraints, UUID support, timezone-aware timestamps. Railway provides managed instances.
- **Railway**: Simple deployment with managed PostgreSQL. Auto-deploy from GitHub.

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL database
- [Vapi account](https://vapi.ai) with API key
- [Groq account](https://console.groq.com) with API key

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd voice-ai-patient-registration
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values:
#   DATABASE_URL=postgresql://user:pass@host:5432/dbname
#   VAPI_API_KEY=your_key
#   GROQ_API_KEY=your_key
#   SERVER_URL=https://your-deployed-url
```

### 3. Initialize Database

```bash
python seed.py
```

### 4. Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Set Up Vapi Assistant

```bash
# After deploying (so SERVER_URL is reachable by Vapi):
python -m app.vapi_assistant
```

This creates the voice assistant in Vapi and assigns it to your phone number.

### 6. Deploy to Railway

```bash
# Connect to Railway
railway login
railway init
railway add --database postgresql

# Set environment variables
railway variables set VAPI_API_KEY=xxx GROQ_API_KEY=xxx SERVER_URL=https://your-app.railway.app

# Deploy
railway up
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/patients` | List all patients. Query params: `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| `GET` | `/patients/:id` | Get patient by UUID |
| `POST` | `/patients` | Create new patient |
| `PUT` | `/patients/:id` | Update patient (partial updates) |
| `DELETE` | `/patients/:id` | Soft-delete (sets `deleted_at`) |

### Response Format

All endpoints return a consistent JSON envelope:

```json
{
  "data": { ... },
  "error": null
}
```

### Example: Create Patient

```bash
curl -X POST https://your-app.railway.app/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "sex": "Female",
    "phone_number": "5551234567",
    "address_line_1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
  }'
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `VAPI_API_KEY` | Yes | Vapi API key |
| `GROQ_API_KEY` | Yes | Groq API key (used by Vapi) |
| `VAPI_PHONE_NUMBER_ID` | Yes | Vapi phone number ID to assign to assistant |
| `SERVER_URL` | Yes | Public URL of deployed backend (for Vapi webhooks) |
| `PORT` | No | Server port (default: 8000) |

## Voice Agent Prompt Engineering

The system prompt (`app/vapi_assistant.py`) is designed for:

1. **Natural conversation flow** — Collects fields in a logical order (name → DOB → sex → phone → address), not a rigid questionnaire.
2. **Validation with re-prompting** — Invalid inputs trigger specific, helpful re-prompts (not generic errors).
3. **Mandatory confirmation** — Agent reads back all data before saving. Caller must confirm.
4. **Duplicate detection** — After collecting phone number, checks for existing patient and offers to update instead.
5. **Graceful edge cases** — Handles corrections, out-of-order responses, spelling requests, and mid-conversation restarts.

## Bonus Features Implemented

- **Duplicate Detection**: Agent checks phone number against existing records and offers to update.
- **Conversation Logging**: All webhook events and patient saves logged to stdout.
- **Seed Data**: 2 demo patients pre-loaded for testing.

## Known Limitations & Trade-offs

1. **No authentication on API** — For a 3-hour assessment, API is open. Production would need JWT/OAuth.
2. **No HIPAA compliance** — As stated in requirements, this is not a production healthcare system.
3. **No call recording/transcript storage** — Vapi records calls but transcripts aren't persisted to our DB.
4. **No dashboard UI** — API-only. Would add a simple React frontend as next step.
5. **Soft-delete only** — No hard delete endpoint, by design (spec requirement).
6. **Single assistant** — One Vapi assistant handles all calls. Production would support multiple concurrent agents.

## Next Steps

If given more time, I would add:

1. **Patient Dashboard** — React/Next.js frontend displaying registered patients.
2. **Call Transcript Storage** — Persist Vapi call transcripts linked to patient records.
3. **Appointment Scheduling** — Mock appointment booking after registration.
4. **Multi-language Support** — Detect language and switch (Vapi supports multilingual).
5. **API Authentication** — JWT-based auth for the REST API.
6. **Automated Tests** — pytest suite for API endpoints and validation logic.
7. **Rate Limiting** — Protect API from abuse.
8. **Webhook Signature Verification** — Validate Vapi webhook authenticity.

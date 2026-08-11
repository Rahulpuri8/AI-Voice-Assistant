"""
Voice AI Patient Registration System
Main FastAPI application entry point.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.routes import patients, vapi_webhook
from app.schemas import APIResponse

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --- Create tables on startup ---
Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI(
    title="Patient Registration API",
    description="Voice AI Agent backend for patient demographic registration",
    version="1.0.0",
)

# --- CORS (allow Vapi and any frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(patients.router)
app.include_router(vapi_webhook.router)


# --- Global exception handler for consistent JSON envelope ---
@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            error=str(exc.detail) if hasattr(exc, "detail") else "Validation error"
        ).model_dump(),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content=APIResponse(error="Resource not found").model_dump(),
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(error="Internal server error").model_dump(),
    )


# --- Health check ---
@app.get("/")
def root():
    return {
        "service": "Patient Registration Voice AI",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

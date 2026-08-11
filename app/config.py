import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/patient_registration")
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    VAPI_PHONE_NUMBER_ID: str = os.getenv("VAPI_PHONE_NUMBER_ID", "")
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

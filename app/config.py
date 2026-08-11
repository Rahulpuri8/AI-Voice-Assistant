import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    _db_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = _db_url
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    VAPI_PHONE_NUMBER_ID: str = os.getenv("VAPI_PHONE_NUMBER_ID", "")
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

import re
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Valid US state abbreviations ---
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "GU", "VI", "AS", "MP",
}


class SexEnum(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    decline = "Decline to Answer"


# --- Base schema with shared validation ---
class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str = Field(..., min_length=1)
    address_line_2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\-']+$", v):
            raise ValueError("Name must contain only letters, hyphens, and apostrophes")
        return v.strip()

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Phone number must be a valid 10-digit U.S. number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in US_STATES:
            raise ValueError(f"Invalid U.S. state abbreviation: {v}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("Zip code must be 5-digit or ZIP+4 format (e.g., 12345 or 12345-6789)")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit U.S. number")
        return digits


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for partial updates — all fields optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z\-']+$", v):
            raise ValueError("Name must contain only letters, hyphens, and apostrophes")
        return v.strip() if v else v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Phone number must be a valid 10-digit U.S. number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper().strip()
        if v not in US_STATES:
            raise ValueError(f"Invalid U.S. state abbreviation: {v}")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("Zip code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit U.S. number")
        return digits


class PatientResponse(BaseModel):
    """Schema for patient API responses."""
    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: Optional[str] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIResponse(BaseModel):
    """Standard API response envelope."""
    data: Optional[object] = None
    error: Optional[str] = None

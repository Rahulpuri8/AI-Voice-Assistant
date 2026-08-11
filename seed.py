"""
Seed the database with 2 demo patient records.
Run: python seed.py
"""

import uuid
from datetime import date, datetime, timezone

from app.database import SessionLocal, engine
from app.models import Base, Patient


def seed():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if seed data already exists
        existing = db.query(Patient).count()
        if existing > 0:
            print(f"Database already has {existing} patient(s). Skipping seed.")
            return

        patients = [
            Patient(
                patient_id=uuid.uuid4(),
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1990, 5, 15),
                sex="Female",
                phone_number="5551234567",
                email="jane.doe@example.com",
                address_line_1="123 Main Street",
                address_line_2="Apt 4B",
                city="Austin",
                state="TX",
                zip_code="78701",
                insurance_provider="Blue Cross Blue Shield",
                insurance_member_id="BCB123456789",
                preferred_language="English",
                emergency_contact_name="John Doe",
                emergency_contact_phone="5559876543",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            Patient(
                patient_id=uuid.uuid4(),
                first_name="Carlos",
                last_name="Rivera",
                date_of_birth=date(1985, 11, 3),
                sex="Male",
                phone_number="5559871234",
                email=None,
                address_line_1="456 Oak Avenue",
                address_line_2=None,
                city="Miami",
                state="FL",
                zip_code="33101",
                insurance_provider=None,
                insurance_member_id=None,
                preferred_language="Spanish",
                emergency_contact_name=None,
                emergency_contact_phone=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        db.add_all(patients)
        db.commit()
        print(f"Seeded {len(patients)} demo patients.")
        for p in patients:
            print(f"  - {p.first_name} {p.last_name} (ID: {p.patient_id})")

    finally:
        db.close()


if __name__ == "__main__":
    seed()

from datetime import date
from .db_config import SessionLocal
from .models import Doctor, Patient, Prescription

# Create DB session
db = SessionLocal()

try:
    # Create Doctor
    doctor = Doctor(
        name="Dr. Sharma",
        specialization="Cardiology",
        license_number="LIC12345",
        hospital_or_clinic="City Hospital",
        phone="9876543210",
        email="drsharma@example.com",
        created_at="2026-02-22"
    )

    # Create Patient
    patient = Patient(
        name="Rahul Verma",
        age=25,
        gender="Male",
        phone="9999999999",
        address="Mumbai",
        date_of_birth="2000-01-01",
        created_at="2026-02-22"
    )

    db.add(doctor)
    db.add(patient)
    db.commit()

    # Create Prescription (Issue + Expiry Date)
    prescription = Prescription(
        doctor_id=doctor.id,
        patient_id=patient.id,
        diagnosis="Fever",
        issue_date=date(2026, 2, 22),
        expiry_date=date(2026, 3, 1),
        blockchain_hash="sample_hash_123",
        is_tampered=False,
        status="Active",
        created_at="2026-02-22"
    )

    db.add(prescription)
    db.commit()

    print("Sample doctor, patient, and prescription inserted successfully!")

except Exception as e:
    print("Error:", e)
    db.rollback()
finally:
    db.close()
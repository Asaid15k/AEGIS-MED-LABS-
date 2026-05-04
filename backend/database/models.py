from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from .db_config import engine

Base = declarative_base()

# ---------------- DOCTORS TABLE ----------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialization = Column(String)
    license_number = Column(String, unique=True, nullable=False)
    hospital_or_clinic = Column(String)
    phone = Column(String)
    email = Column(String)
    created_at = Column(String)

    prescriptions = relationship("Prescription", back_populates="doctor")


# ---------------- PATIENTS TABLE ----------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    address = Column(String)
    date_of_birth = Column(String)
    created_at = Column(String)

    prescriptions = relationship("Prescription", back_populates="patient")


# ---------------- MEDICINES TABLE ----------------
class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, nullable=False)
    manufacturer = Column(String)
    dosage_form = Column(String)
    strength = Column(String)
    description = Column(String)


# ---------------- PRESCRIPTIONS TABLE ----------------
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    diagnosis = Column(String)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)

    blockchain_hash = Column(String)
    is_tampered = Column(Boolean, default=False)
    verification_status = Column(String, default="Valid")
    last_verified_at = Column(String)

    status = Column(String, default="Active")
    notes = Column(String)
    created_at = Column(String)

    doctor = relationship("Doctor", back_populates="prescriptions")
    patient = relationship("Patient", back_populates="prescriptions")
    qr_code = relationship("QRCode", back_populates="prescription", uselist=False)


# ---------------- QR CODE TABLE ----------------
class QRCode(Base):
    __tablename__ = "qrcodes"

    id = Column(Integer, primary_key=True, index=True)
    qr_value = Column(String, unique=True, nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), unique=True)
    generated_at = Column(String)
    is_active = Column(Boolean, default=True)

    prescription = relationship("Prescription", back_populates="qr_code")


# ---------------- PRESCRIPTION MEDICINES ----------------
class PrescriptionMedicine(Base):
    __tablename__ = "prescription_medicines"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)

    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    instructions = Column(String)


# ---------------- VERIFICATION LOGS ----------------
class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    scan_time = Column(String)
    scan_location = Column(String)
    verification_result = Column(String)
    risk_score = Column(String)
    scanned_by = Column(String)
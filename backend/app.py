from qr_service import compute_hash, generate_qr
from blockchain import store_hash, get_hash
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date
import uuid

# YOUR DATABASE IMPORTS (kept exactly as your project)
from database.db_config import SessionLocal
from database.models import Doctor, Patient, Prescription, QRCode, Medicine

app = FastAPI(title="Secure Digital Prescription Integrity System")

# ---------------- CORS (MANDATORY FOR FRONTEND CONNECTION) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend (HTML/JS)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- Pydantic Schemas ----------------
class DoctorCreate(BaseModel):
    name: str
    specialization: str
    license_number: str
    hospital_or_clinic: str
    phone: str
    email: str

class DoctorLogin(BaseModel):
    email: str
    license_number: str

class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    address: str

class PrescriptionCreate(BaseModel):
    doctor_id: int
    patient_id: int
    diagnosis: str
    issue_date: date
    expiry_date: date

# ---------------- ROOT API (TEST BACKEND) ----------------
@app.get("/")
def root():
    return {"message": "Backend is running and connected to PostgreSQL database"}

# ---------------- ADD DOCTOR (REGISTER FROM FRONTEND) ----------------
@app.post("/doctors")
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    
    # Check duplicate email or license (professional feature)
    existing_doctor = db.query(Doctor).filter(
        (Doctor.email == doctor.email) | 
        (Doctor.license_number == doctor.license_number)
    ).first()

    if existing_doctor:
        raise HTTPException(
            status_code=400,
            detail="Doctor with this email or license number already exists"
        )

    new_doctor = Doctor(
        name=doctor.name,
        specialization=doctor.specialization,
        license_number=doctor.license_number,
        hospital_or_clinic=doctor.hospital_or_clinic,
        phone=doctor.phone,
        email=doctor.email,
        created_at=str(date.today())
    )

    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)

    print("Doctor saved to database:", new_doctor.name)

    return {
        "message": "Doctor registered successfully",
        "doctor_id": new_doctor.id
    }

# ---------------- DOCTOR LOGIN (FOR LOGIN PAGE) ----------------
@app.post("/doctor-login")
def doctor_login(data: DoctorLogin, db: Session = Depends(get_db)):
    
    doctor = db.query(Doctor).filter(
        Doctor.email == data.email,
        Doctor.license_number == data.license_number
    ).first()

    if not doctor:
        raise HTTPException(status_code=401, detail="Invalid email or license number")

    return {
        "message": "Login successful",
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "specialization": doctor.specialization
    }

# ---------------- ADD PATIENT ----------------
@app.post("/patients")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    
    new_patient = Patient(
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        address=patient.address,
        created_at=str(date.today())
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    print("Patient saved to database:", new_patient.name)

    return {
        "message": "Patient created successfully",
        "patient_id": new_patient.id
    }

# ---------------- CREATE PRESCRIPTION + UNIQUE QR + BLOCKCHAIN HASH ----------------
@app.post("/prescriptions")
def create_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    
    # Validate doctor
    doctor = db.query(Doctor).filter(Doctor.id == prescription.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Validate patient
    patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ✅ Generate blockchain hash (FIXED)
    import hashlib
    blockchain_hash = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    blockchain_hash_bytes = bytes.fromhex(blockchain_hash)

    # Create prescription
    new_prescription = Prescription(
        doctor_id=prescription.doctor_id,
        patient_id=prescription.patient_id,
        diagnosis=prescription.diagnosis,
        issue_date=prescription.issue_date,
        expiry_date=prescription.expiry_date,
        blockchain_hash=blockchain_hash,
        is_tampered=False,
        verification_status="Valid",
        status="Active",
        created_at=str(date.today())
    )

    # SAVE TO DB
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    # ✅ STORE ON BLOCKCHAIN (FIXED)
    store_hash(new_prescription.id, blockchain_hash_bytes)

    # GENERATE QR
    unique_qr_value = str(uuid.uuid4())

    qr_code = QRCode(
        qr_value=unique_qr_value,
        prescription_id=new_prescription.id,
        generated_at=str(date.today()),
        is_active=True
    )

    db.add(qr_code)
    db.flush()   # IMPORTANT
    db.commit()

    print("Prescription + QR stored:", unique_qr_value)

    return {
        "message": "Prescription created successfully",
        "prescription_id": new_prescription.id,
        "qr_code": unique_qr_value,
        "blockchain_hash": blockchain_hash
    }

# ---------------- GET ALL DOCTORS (FOR FRONTEND DROPDOWN) ----------------
@app.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return doctors

# ---------------- GET ALL PATIENTS ----------------
@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

# ---------------- GET ALL PRESCRIPTIONS ----------------
@app.get("/prescriptions")
def get_prescriptions(db: Session = Depends(get_db)):
    prescriptions = db.query(Prescription).all()
    return prescriptions

# ---------------- VERIFY QR (FOR PHARMACIST / VERIFY PAGE) ----------------
@app.get("/verify/{qr_value}")
def verify_qr(qr_value: str, db: Session = Depends(get_db)):
    
    qr = db.query(QRCode).filter(QRCode.qr_value == qr_value).first()

    if not qr:
        raise HTTPException(status_code=404, detail="Invalid QR Code")

    prescription = db.query(Prescription).filter(
        Prescription.id == qr.prescription_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return {
        "status": "Valid Prescription",
        "prescription_id": prescription.id,
        "doctor_id": prescription.doctor_id,
        "patient_id": prescription.patient_id,
        "diagnosis": prescription.diagnosis,
        "issue_date": prescription.issue_date,
        "expiry_date": prescription.expiry_date,
        "verification_status": prescription.verification_status
    }
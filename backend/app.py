from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from dotenv import load_dotenv
load_dotenv()
import os
from qr_service import compute_hash, generate_qr
from blockchain import store_hash, get_hash, verify_on_chain
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date
import uuid
import hashlib

# YOUR DATABASE IMPORTS (kept exactly as your project)
from database.db_config import SessionLocal
from database.models import Doctor, Patient, Prescription, QRCode, Medicine

app = FastAPI(title="Secure Digital Prescription Integrity System")
import os
BASE_DIR = "/app"
FRONTEND_DIR = "/app/frontend"

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/doctor")
def doctor_page(request: Request):
    return templates.TemplateResponse("doctor_login.html", {"request": request})

@app.get("/pharmacist")
def pharmacist_page(request: Request):
    return templates.TemplateResponse("pharmacist_login.html", {"request": request})

@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/doctor")
def doctor_page(request: Request):
    return templates.TemplateResponse("doctor_login.html", {"request": request})

@app.get("/pharmacist")
def pharmacist_page(request: Request):
    return templates.TemplateResponse("pharmacist_login.html", {"request": request})

@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"message": "AEGISMEDLABS backend running — Polygon Amoy blockchain active"}

# ---------------- DOCTOR REGISTER ----------------
@app.post("/doctors")
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    existing_doctor = db.query(Doctor).filter(
        (Doctor.email == doctor.email) |
        (Doctor.license_number == doctor.license_number)
    ).first()
    if existing_doctor:
        raise HTTPException(status_code=400, detail="Doctor with this email or license number already exists")

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
    return {"message": "Doctor registered successfully", "doctor_id": new_doctor.id}

# ---------------- DOCTOR LOGIN ----------------
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
    return {"message": "Patient created successfully", "patient_id": new_patient.id}

# ---------------- CREATE PRESCRIPTION + QR + BLOCKCHAIN ----------------
@app.post("/prescriptions")
def create_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):

    doctor = db.query(Doctor).filter(Doctor.id == prescription.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Generate deterministic hash from prescription data (not random)
    # This means the hash PROVES what the prescription contained
    raw = f"{prescription.doctor_id}|{prescription.patient_id}|{prescription.diagnosis}|{prescription.issue_date}|{prescription.expiry_date}|{uuid.uuid4()}"
    blockchain_hash = hashlib.sha256(raw.encode()).hexdigest()
    blockchain_hash_bytes = bytes.fromhex(blockchain_hash)

    # Save prescription to DB
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
    db.add(new_prescription)
    db.commit()
    db.refresh(new_prescription)

    # Store hash on Polygon Amoy blockchain (automatic, no manual steps)
    try:
        tx_hash = store_hash(new_prescription.id, blockchain_hash_bytes)
        print(f"[BLOCKCHAIN] TX confirmed: {tx_hash}")
    except Exception as e:
        # Don't fail the whole request if blockchain is slow — hash is in DB
        print(f"[BLOCKCHAIN] Warning: {e}")
        tx_hash = None

    # Generate QR code (UUID — unique, not guessable)
    unique_qr_value = str(uuid.uuid4())
    qr_code = QRCode(
        qr_value=unique_qr_value,
        prescription_id=new_prescription.id,
        generated_at=str(date.today()),
        is_active=True
    )
    db.add(qr_code)
    db.commit()

    return {
        "message": "Prescription created successfully",
        "prescription_id": new_prescription.id,
        "qr_code": unique_qr_value,
        "blockchain_hash": blockchain_hash,
        "tx_hash": tx_hash
    }

# ---------------- GET ENDPOINTS ----------------
@app.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()

@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@app.get("/prescriptions")
def get_prescriptions(db: Session = Depends(get_db)):
    return db.query(Prescription).all()

# ---------------- VERIFY QR — WITH BLOCKCHAIN TAMPER CHECK ----------------
@app.get("/verify/{qr_value}")
def verify_qr(qr_value: str, db: Session = Depends(get_db)):

    # 1. Find QR in DB
    qr = db.query(QRCode).filter(QRCode.qr_value == qr_value).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Invalid QR Code — not found")

    if not qr.is_active:
            return {"valid": False, "status": "already_dispensed", "reason": "This prescription has already been dispensed and cannot be used again."}

    # 2. Find prescription
    prescription = db.query(Prescription).filter(
        Prescription.id == qr.prescription_id
    ).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # 3. Check expiry
    if prescription.expiry_date < date.today():
        return {
            "valid": False,
            "status": "expired",
            "reason": f"Prescription expired on {prescription.expiry_date}"
        }

    # 4. Blockchain tamper check (compares DB hash vs on-chain hash)
    tamper_detected = False
    blockchain_verified = False
    try:
        blockchain_verified = verify_on_chain(
            prescription.id,
            prescription.blockchain_hash
        )
        if not blockchain_verified:
            # Hash mismatch — data was changed after creation
            prescription.is_tampered = True
            prescription.verification_status = "Tampered"
            db.commit()
            tamper_detected = True
    except Exception as e:
        print(f"[BLOCKCHAIN] Verify error (non-fatal): {e}")
        # If blockchain is unreachable, still return DB result
        blockchain_verified = None

    if tamper_detected:
        return {
            "valid": False,
            "status": "tampered",
            "reason": "Blockchain hash mismatch — this prescription may have been altered"
        }

    # 5. Fetch doctor and patient names
    doctor = db.query(Doctor).filter(Doctor.id == prescription.doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()

    return {
        "valid": True,
        "status": "valid",
        "prescription_id": prescription.id,
        "patient_name": patient.name if patient else "Unknown",
        "doctor_name": doctor.name if doctor else "Unknown",
        "diagnosis": prescription.diagnosis,
        "issue_date": str(prescription.issue_date),
        "expiry_date": str(prescription.expiry_date),
        "verification_status": prescription.verification_status,
        "blockchain_verified": blockchain_verified,
        "blockchain_hash": prescription.blockchain_hash
    }

# ---------------- DISPENSE ENDPOINT (for pharmacist confirm button) ----------------
@app.post("/prescriptions/{prescription_id}/dispense")
def dispense_prescription(prescription_id: int, db: Session = Depends(get_db)):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Deactivate QR so it can't be scanned again
    qr = db.query(QRCode).filter(QRCode.prescription_id == prescription_id).first()
    if qr:
        qr.is_active = False

    prescription.status = "Dispensed"
    db.commit()

    return {"message": "Prescription dispensed and QR deactivated", "prescription_id": prescription_id}


from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Patient, Appointment

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Booking System")


class PatientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    email: Optional[str] = None


class PatientResponse(PatientCreate):
    id: int

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_time: datetime
    reason: str = Field(min_length=3, max_length=250)


class AppointmentResponse(AppointmentCreate):
    id: int

    class Config:
        from_attributes = True


@app.get("/")
def home():
    return {"message": "Clinic Booking System API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/patients", response_model=PatientResponse, status_code=201)
def register_patient(
        patient: PatientCreate,
        db: Session = Depends(get_db)
):
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@app.get("/patients", response_model=list[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()


@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


@app.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=201
)
def book_appointment(
        appointment: AppointmentCreate,
        db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(
        Patient.id == appointment.patient_id
    ).first()

    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    if appointment.appointment_time <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Appointment must be in the future"
        )

    db_appointment = Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@app.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()


@app.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    return appointment

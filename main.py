
from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Patient, Doctor, Appointment
from sqlalchemy import inspect, text

# Base.metadata.create_all(bind=engine)

Base.metadata.create_all(bind=engine)

# Add new columns to an existing SQLite database safely.
existing_columns = {
    column["name"]
    for column in inspect(engine).get_columns("appointments")
}

new_columns = {
    "doctor_id": "INTEGER",
    "status": "VARCHAR(20) NOT NULL DEFAULT 'booked'",
    "cancellation_reason": "VARCHAR(250)",
}

with engine.begin() as connection:
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE appointments "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )

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
    doctor_id: int
    appointment_time: datetime
    reason: str = Field(min_length=3, max_length=250)
# class AppointmentCreate(BaseModel):
#     patient_id: int
#     appointment_time: datetime
#     reason: str = Field(min_length=3, max_length=250)

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    appointment_time: datetime
    reason: str
    status: str = "booked"
    cancellation_reason: Optional[str] = None

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
# def book_appointment(
#         appointment: AppointmentCreate,
#         db: Session = Depends(get_db)
# ):
#     patient = db.query(Patient).filter(
#         Patient.id == appointment.patient_id
#     ).first()
#
#     if patient is None:
#         raise HTTPException(status_code=404, detail="Patient not found")
#
#     if appointment.appointment_time <= datetime.now():
#         raise HTTPException(
#             status_code=400,
#             detail="Appointment must be in the future"
#         )
#
#     db_appointment = Appointment(**appointment.model_dump())
#     db.add(db_appointment)
#     db.commit()
#     db.refresh(db_appointment)
#     return db_appointment


def book_appointment(
        appointment: AppointmentCreate,
        db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.id == appointment.patient_id
    ).first()

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id
    ).first()

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    slot = appointment.appointment_time

    if slot <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Appointment must be in the future",
        )

    if slot.second != 0 or slot.microsecond != 0:
        raise HTTPException(
            status_code=400,
            detail="Appointment must start on a 30-minute slot",
        )

    if slot.minute not in (0, 30):
        raise HTTPException(
            status_code=400,
            detail="Appointment must start on a 30-minute slot",
        )

    if slot.weekday() not in [
        int(day) for day in doctor.working_days.split(",")
    ]:
        raise HTTPException(
            status_code=400,
            detail="Doctor does not work on this day",
        )

    working_start = time.fromisoformat(doctor.working_start)
    working_end = time.fromisoformat(doctor.working_end)

    if not (
            working_start <= slot.time()
            and (slot + timedelta(minutes=30)).time() <= working_end
    ):
        raise HTTPException(
            status_code=400,
            detail="Appointment is outside the doctor's working hours",
        )

    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_time == slot,
        Appointment.status == "booked",
        ).first()

    if conflict is not None:
        raise HTTPException(
            status_code=409,
            detail="This appointment slot is already booked",
        )

    db_appointment = Appointment(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_time=appointment.appointment_time,
        reason=appointment.reason,
        status="booked",
    )

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

from datetime import date, datetime, time, timedelta


@app.post("/doctors", status_code=201)
def create_doctor(
        name: str,
        working_start: str = "09:00",
        working_end: str = "17:00",
        working_days: str = "0,1,2,3,4",
        db: Session = Depends(get_db),
):
    try:
        start = time.fromisoformat(working_start)
        end = time.fromisoformat(working_end)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Working hours must use HH:MM format",
        )

    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="Working start must be earlier than working end",
        )

    doctor = Doctor(
        name=name,
        working_start=working_start,
        working_end=working_end,
        working_days=working_days,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return {
        "id": doctor.id,
        "name": doctor.name,
        "working_start": doctor.working_start,
        "working_end": doctor.working_end,
        "working_days": doctor.working_days,
    }


@app.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()


@app.get("/doctors/{doctor_id}/availability")
def get_doctor_availability(
        doctor_id: int,
        appointment_date: date,
        db: Session = Depends(get_db),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if appointment_date.weekday() not in [
        int(day) for day in doctor.working_days.split(",")
    ]:
        return {"doctor_id": doctor_id, "date": str(appointment_date), "available_slots": []}

    start = datetime.combine(
        appointment_date, time.fromisoformat(doctor.working_start)
    )
    end = datetime.combine(
        appointment_date, time.fromisoformat(doctor.working_end)
    )

    now = datetime.now()
    available_slots = []
    slot = start

    while slot + timedelta(minutes=30) <= end:
        slot_end = slot + timedelta(minutes=30)

        if slot > now:
            conflict = (
                db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_time == slot,
                    Appointment.status == "booked",
                    )
                .first()
            )

            if conflict is None:
                available_slots.append({
                    "start": slot.isoformat(),
                    "end": slot_end.isoformat(),
                })

        slot += timedelta(minutes=30)

    return {
        "doctor_id": doctor_id,
        "date": str(appointment_date),
        "available_slots": available_slots,
    }

@app.patch("/appointments/{appointment_id}/cancel")
def cancel_appointment(
        appointment_id: int,
        reason: str,
        db: Session = Depends(get_db),
):
    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Appointment is already cancelled",
        )

    if not reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Cancellation reason is required",
        )

    appointment.status = "cancelled"
    appointment.cancellation_reason = reason

    db.commit()
    db.refresh(appointment)

    return {
        "message": "Appointment cancelled successfully",
        "appointment_id": appointment.id,
        "status": appointment.status,
        "cancellation_reason": appointment.cancellation_reason,
    }

@app.patch("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
        appointment_id: int,
        new_appointment_time: datetime,
        db: Session = Depends(get_db),
):
    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cannot reschedule a cancelled appointment",
        )

    doctor = (
        db.query(Doctor)
        .filter(Doctor.id == appointment.doctor_id)
        .first()
    )

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    slot = new_appointment_time

    if slot <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Appointment must be in the future",
        )

    if slot.second != 0 or slot.microsecond != 0 or slot.minute not in (0, 30):
        raise HTTPException(
            status_code=400,
            detail="Appointment must start on a 30-minute slot",
        )

    if slot.weekday() not in [
        int(day) for day in doctor.working_days.split(",")
    ]:
        raise HTTPException(
            status_code=400,
            detail="Doctor does not work on this day",
        )

    working_start = time.fromisoformat(doctor.working_start)
    working_end = time.fromisoformat(doctor.working_end)

    if not (
            working_start <= slot.time()
            and (slot + timedelta(minutes=30)).time() <= working_end
    ):
        raise HTTPException(
            status_code=400,
            detail="Appointment is outside the doctor's working hours",
        )

    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_time == slot,
            Appointment.status == "booked",
            Appointment.id != appointment.id,
            )
        .first()
    )

    if conflict is not None:
        raise HTTPException(
            status_code=409,
            detail="The requested appointment slot is already booked",
        )

    appointment.appointment_time = slot

    db.commit()
    db.refresh(appointment)

    return {
        "message": "Appointment rescheduled successfully",
        "appointment_id": appointment.id,
        "new_appointment_time": appointment.appointment_time,
        "status": appointment.status,
    }




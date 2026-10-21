
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=True)

    appointments = relationship(
        "Appointment",
        back_populates="patient"
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    reason = Column(String(250), nullable=False)

    patient = relationship(
        "Patient",
        back_populates="appointments"
    )

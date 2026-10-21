
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def create_patient():
    response = client.post(
        "/patients",
        json={
            "name": "Test Patient",
            "phone": "0712345678",
            "email": "patient@example.com",
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def create_doctor():
    response = client.post(
        "/doctors",
        params={
            "name": "Dr Test",
            "working_start": "09:00",
            "working_end": "17:00",
            "working_days": "0,1,2,3,4,5,6",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def future_slot():
    slot = datetime.now().replace(
        second=0, microsecond=0, minute=0
    ) + timedelta(days=2)
    while slot.weekday() < 0:
        slot += timedelta(days=1)
    return slot.replace(hour=10, minute=0)


def book_appointment(patient_id, doctor_id, slot):
    return client.post(
        "/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_time": slot.isoformat(),
            "reason": "General consultation",
        },
    )


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_patients():
    response = client.get("/patients")
    assert response.status_code == 200


def test_list_appointments():
    response = client.get("/appointments")
    assert response.status_code == 200


def test_book_appointment_successfully():
    patient_id = create_patient()
    doctor_id = create_doctor()

    response = book_appointment(
        patient_id, doctor_id, future_slot()
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "booked"


def test_prevent_double_booking():
    patient_id = create_patient()
    doctor_id = create_doctor()
    slot = future_slot()

    first = book_appointment(patient_id, doctor_id, slot)
    second = book_appointment(patient_id, doctor_id, slot)

    assert first.status_code == 201, first.text
    assert second.status_code == 409, second.text


def test_reject_invalid_appointment_time():
    patient_id = create_patient()
    doctor_id = create_doctor()
    slot = future_slot().replace(minute=15)

    response = book_appointment(patient_id, doctor_id, slot)

    assert response.status_code == 400, response.text


def test_cancel_appointment():
    patient_id = create_patient()
    doctor_id = create_doctor()

    booked = book_appointment(
        patient_id, doctor_id, future_slot()
    )
    assert booked.status_code == 201, booked.text
    appointment_id = booked.json()["id"]

    response = client.patch(
        f"/appointments/{appointment_id}/cancel",
        params={"reason": "Patient requested cancellation"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"


def test_prevent_double_cancellation():
    patient_id = create_patient()
    doctor_id = create_doctor()

    booked = book_appointment(
        patient_id, doctor_id, future_slot()
    )
    assert booked.status_code == 201, booked.text
    appointment_id = booked.json()["id"]

    first = client.patch(
        f"/appointments/{appointment_id}/cancel",
        params={"reason": "Patient requested cancellation"},
    )
    second = client.patch(
        f"/appointments/{appointment_id}/cancel",
        params={"reason": "Patient requested cancellation"},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 400, second.text


def test_reschedule_appointment():
    patient_id = create_patient()
    doctor_id = create_doctor()
    original_slot = future_slot()

    booked = book_appointment(
        patient_id, doctor_id, original_slot
    )
    assert booked.status_code == 201, booked.text
    appointment_id = booked.json()["id"]

    new_slot = original_slot + timedelta(minutes=30)

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule",
        params={"new_appointment_time": new_slot.isoformat()},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "booked"
    assert datetime.fromisoformat(
        response.json()["new_appointment_time"]
    ) == new_slot


def test_doctor_availability():
    doctor_id = create_doctor()
    slot = future_slot()

    response = client.get(
        f"/doctors/{doctor_id}/availability",
        params={"appointment_date": slot.date().isoformat()},
    )

    assert response.status_code == 200, response.text
    assert "available_slots" in response.json()


from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


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

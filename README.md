# Clinic Booking System API

A RESTful clinic booking API built with Python, FastAPI, SQLAlchemy, and SQLite. The application supports patient registration, patient retrieval, appointment booking, and appointment retrieval.

## 1. Live Application

- **API base URL:** https://clinic-interview-system.onrender.com/
- **Interactive API documentation:** https://clinic-interview-system.onrender.com/docs
- **Health check:** https://clinic-interview-system.onrender.com/health
- **Source code:** https://github.com/waitara/ClinicInterviewSystem

## 2. Technology Stack

- Python
- FastAPI
- SQLAlchemy ORM
- SQLite
- Pydantic request validation
- Pytest and HTTPX
- GitHub Actions for automated testing
- Render for cloud deployment

## 3. Features

- Register patients.
- Retrieve all patients.
- Retrieve a patient by ID.
- Book appointments for existing patients.
- Validate appointment details.
- Reject appointments scheduled in the past.
- Retrieve all appointments.
- Retrieve an appointment by ID.
- Provide interactive API documentation.
- Run automated tests through GitHub Actions.

## 4. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| POST | `/patients` | Register a patient |
| GET | `/patients` | List all patients |
| GET | `/patients/{patient_id}` | Retrieve a patient |
| POST | `/appointments` | Book an appointment |
| GET | `/appointments` | List all appointments |
| GET | `/appointments/{appointment_id}` | Retrieve an appointment |

Successful patient registration and appointment booking return `201 Created`. Missing records return `404 Not Found`, and invalid appointment dates return `400 Bad Request`.

## 5. Run Locally

### Prerequisites

- Python 3.12 or a compatible Python version
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/waitara/ClinicInterviewSystem.git
cd ClinicInterviewSystem
```

Create and activate a virtual environment on Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload
```

Open the interactive documentation at `http://127.0.0.1:8000/docs`.

## 6. Automated Testing

Run the test suite locally:

```bash
python -m pytest -v
```

GitHub Actions is configured to run automated tests on pushes and pull requests targeting the `main` branch.

## 7. Cloud Deployment and CI/CD

The application is deployed on Render. The service is configured to install dependencies from `requirements.txt` and start FastAPI using Uvicorn.

Render automatic deployment is configured for commits to the `main` branch. GitHub Actions separately executes the automated tests.

**Note:** Automatic deployment and automated testing are configured as separate workflows. Deployment is not currently guaranteed to wait for successful test completion.

## 8. Database and Persistence Limitation

The application currently uses SQLite with a local database file named `clinic.db`.

The API has been tested on the deployed environment, including patient registration, appointment booking, and retrieval of the created records.

The current Render Free compute plan does not support persistent disks. Consequently, SQLite data stored on the service's local filesystem may be lost when the instance restarts or is redeployed. Data persistence across restarts has not been verified.

For production use, the recommended improvement is to migrate to a managed PostgreSQL database or another durable database service. Database credentials should be supplied through environment variables, and migrations and backup procedures should be implemented.

## 9. Future Improvements

- Use a managed database with durable storage.
- Add authentication and role-based access control.
- Prevent conflicting appointments and double-booking.
- Add appointment updates and cancellation.
- Improve test coverage for validation and error handling.
- Require successful automated checks before deployment.

## 10. Project Status

The deployed API is operational, and the core patient and appointment workflows have been verified. Database durability on the Render Free plan remains a documented limitation.

# Clinic Booking System API

A RESTful clinic booking API built with Python, FastAPI, SQLAlchemy, and SQLite. The system supports patient management, doctor management, appointment booking, availability checking, cancellation, and rescheduling.

## 1. Live Application

- API base URL: https://clinic-interview-system.onrender.com/
- Interactive API documentation: https://clinic-interview-system.onrender.com/docs
- Health check: https://clinic-interview-system.onrender.com/health
- Source code: https://github.com/waitara/ClinicInterviewSystem

## 2. Technology Stack

- Python
- FastAPI for REST API development
- SQLAlchemy ORM for database access
- SQLite for data storage
- Pydantic for request validation
- Pytest and HTTPX for automated testing
- GitHub Actions for continuous integration
- Render for cloud deployment

## 3. Features

### Patient management
- Register patients.
- Retrieve all patients.
- Retrieve an individual patient by ID.

### Doctor management
- Register doctors and configure their working hours.
- Configure working days.
- Retrieve doctors.
- Retrieve available 30-minute appointment slots for a specified date.

### Appointment management
- Book appointments for existing patients and doctors.
- Validate appointment dates, times, and working hours.
- Reject bookings for occupied appointment slots.
- Retrieve appointments.
- Cancel appointments with a recorded reason.
- Prevent repeat cancellation.
- Reschedule booked appointments to available slots.
- Reject attempts to reschedule cancelled appointments.
- Return meaningful HTTP status codes for common errors.

## 4. System Architecture and Design

The application uses a layered architecture to separate HTTP request handling, validation, business logic, and database operations.

### Main components

1. API layer (`main.py`): Defines FastAPI routes, receives requests, validates inputs, executes booking rules, and returns HTTP responses.
2. Data model layer (`models.py`): Defines SQLAlchemy entities and relationships for patients, doctors, and appointments.
3. Database layer (`database.py`): Configures the SQLAlchemy engine, session management, database connection, and declarative base.
4. Validation layer: Uses Pydantic schemas to validate request data and enforce input constraints.
5. Testing layer (`test_main.py`): Uses FastAPI's `TestClient` and pytest to verify API behaviour.
6. Deployment and CI layer: Render hosts the application, while GitHub Actions executes automated tests.

### Data model

- Patient: Stores patient details, including name, phone number, and optional email.
- Doctor: Stores the doctor's name, working hours, and working days.
- Appointment: Stores the patient reference, doctor reference, appointment time, reason, status, and optional cancellation reason.

An appointment belongs to a patient and may be associated with a doctor. The application uses foreign-key relationships to connect records.

### Key design decisions and trade-offs

- FastAPI: Provides automatic request validation, HTTP routing, and OpenAPI documentation. This supports rapid development and makes endpoints easy to test.

- SQLAlchemy: Separates application logic from direct SQL operations and supports a structured model of the domain.

- SQLite: Provides a lightweight database that is easy to configure and run locally. However, a local SQLite file on ephemeral cloud storage is not suitable for reliable production persistence.

- 30-minute appointment slots: Provide a consistent scheduling interval and simplify availability calculations.

- HTTP status codes: Distinguish successful operations from invalid requests, missing records, and scheduling conflicts. For example, `201 Created` indicates a successful booking, `400 Bad Request` indicates an invalid operation, `404 Not Found` indicates a missing record, and `409 Conflict` indicates an occupied slot.

- Dependency injection: FastAPI database dependencies allow database sessions to be supplied to endpoints and overridden during testing.

### Current limitations

The current implementation uses SQLite and does not provide production-grade authentication, role-based authorization, or a managed durable database. The scheduling implementation should also be strengthened with database-level concurrency protection to prevent simultaneous requests from booking the same slot.

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| POST | `/patients` | Register a patient |
| GET | `/patients` | List patients |
| GET | `/patients/{patient_id}` | Retrieve a patient |
| POST | `/doctors` | Register a doctor |
| GET | `/doctors` | List doctors |
| GET | `/doctors/{doctor_id}/availability` | Retrieve available slots for a date |
| POST | `/appointments` | Book an appointment |
| GET | `/appointments` | List appointments |
| GET | `/appointments/{appointment_id}` | Retrieve an appointment |
| PATCH | `/appointments/{appointment_id}/cancel` | Cancel an appointment |
| PATCH | `/appointments/{appointment_id}/reschedule` | Reschedule an appointment |

For request parameters and response schemas, consult the live Swagger documentation.

## 6. Run Locally

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

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
uvicorn main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## 7. Automated Testing

Run the test suite:

```bash
python -m pytest -v
```

The current test suite contains 11 passing tests covering basic API responses, patient and appointment endpoints, booking validation, duplicate-booking prevention, availability retrieval, cancellation, and rescheduling.

GitHub Actions is configured to run automated tests on pushes and pull requests targeting the `main` branch.

## 8. Cloud Deployment and CI/CD

The application is hosted on Render. The service installs dependencies from `requirements.txt` and starts FastAPI using Uvicorn.

GitHub Actions executes the automated test suite. Render is configured to deploy commits from the `main` branch.

CI/CD limitation: Testing and deployment currently operate as separate workflows. The current configuration does not guarantee that deployment waits for successful automated tests. A future improvement is to enforce a successful CI check before merging and deploying changes.

## 9. Database and Persistence

The application currently uses SQLite with a database file named `clinic.db`.

The deployed API has been verified, including successful patient registration, appointment booking, cancellation, and rescheduling requests.

The Render Free service does not provide a persistent disk by default. Consequently, database records stored on the local filesystem may be lost after a restart or redeployment. Durable persistence across restarts has not been verified.

For production use, the recommended improvement is to migrate to managed PostgreSQL or another durable database service, configure credentials through environment variables, and implement database migrations and backups.

## 10. AI Usage Reflection

This section documents how AI assistance was used during development. It should be reviewed and adjusted to reflect the developer's actual experience.

### 1. How was AI used during the assessment?

AI assistance was used to understand the assessment requirements, plan implementation steps, troubleshoot FastAPI errors, develop API endpoints, and improve automated test coverage. It was also used to review documentation and clarify HTTP status codes and scheduling validation.

The application was run and tested locally, and changes were pushed to GitHub and deployed to Render.

### 2. What was one helpful AI suggestion?

A useful suggestion was to test the booking workflow with valid requests, duplicate bookings, and invalid appointment times. This made it possible to verify successful booking (`201`), conflict handling (`409`), and validation failures (`400`) through the API documentation.

### 3. What was one incorrect or incomplete AI output, and how was it identified?

During development, the API documentation returned an internal server error when FastAPI generated `/openapi.json`. The traceback identified an unresolved `AppointmentCreate` type reference. Reviewing the class definition and its placement in `main.py` helped resolve the issue.

This reinforced the importance of inspecting error messages, testing changes, and validating AI-assisted suggestions instead of accepting them without verification.

### 4. What were two decisions made without AI, and why?

**Decision 1 — Using SQLite for the initial implementation:** SQLite was retained to keep local setup simple and minimise infrastructure requirements during development. The persistence limitations of the cloud environment were documented, and managed PostgreSQL was identified as a future improvement.

**Decision 2 — Testing the API through both automated tests and Swagger:** Automated tests provide repeatable checks, while Swagger enables direct inspection of requests, responses, and status codes. Using both approaches helped verify behaviour during implementation and deployment.

## 11. Future Improvements

- Migrate to managed PostgreSQL with durable storage.
- Add authentication and role-based access control.
- Add database constraints and transaction-safe booking to prevent concurrent double-booking.
- Expand automated tests for all validation and error-handling scenarios.
- Add a one-hour booking cutoff rule if required by the business specification.
- Implement a CI/CD pipeline that gates deployment on successful tests.
- Add structured logging, monitoring, and database backup procedures.

## 12. Project Status

The application has been deployed to Render, and the current local automated test suite reports 11 passing tests. The principal appointment workflows have also been manually exercised through Swagger.

Remaining production considerations include durable database persistence, stronger concurrency controls, authentication, and enforcing successful CI checks before deployment.

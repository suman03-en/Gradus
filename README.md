# Gradus Backend API: Internal Mark Evaluation System
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/suman03-en/Gradus)

Gradus is a Django REST API for managing classroom assessments, tracking student performance, and streamlining internal mark workflows for teachers and students.

The backend provides secure authentication, classroom operations, task lifecycle management, grading, and performance insights through role-based APIs.

## Key Features

### Authentication and Account Management

- Secure login and logout workflow.
- Role-aware user management with teacher/student behavior driven by `is_student` in the custom user model.
- Profile creation and editing support based on user role.
- Read-only profile lookup by username.
- OTP-based password reset flow.

### Classroom Management

- Create and manage classrooms.
- Join classroom flow for students.
- Classroom detail view with contextual classroom information.
- Teacher capability to add students by roll number.
- One-subject-per-classroom model for clear academic mapping.

### Task and Assessment Management

- Teachers can create multiple evaluation items, including assignments, offline assessments, and tutorials.
- Students can view tasks available in their classrooms.
- Strictly permissioned task retrieval, update, and deletion.
- Submission support for online-mode tasks.
- Submission time validation to enforce deadlines.

### Grading and Performance Tracking

- Teacher grading workflow for student submissions.
- Students can view marks received for tasks.
- Dashboard support for class-wise percentage/mark insights.

## Tech Stack

### Backend

- Python, Django, Django REST Framework
- SQLite (development), PostgreSQL-ready via `psycopg2-binary`
- CORS support, static/media handling, production serving with Gunicorn + WhiteNoise
- Storage integrations available via `django-storages` (S3/Azure SDKs present)

## Project Structure

- `backend/` - Django project and apps (`accounts`, `classrooms`, `tasks`, `resources`, `apiv1`)

## Local Setup

### Prerequisites

- Python 3.11+

### Backend (Django)

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python backend/manage.py migrate
```

4. Run the backend server:

```bash
python backend/manage.py runserver
```

Backend runs at `http://127.0.0.1:8000` by default.

## API Highlights

Available endpoints include authentication, profile, and classroom flows such as:

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/login/`
- `POST /api/v1/accounts/logout/`
- `GET/PATCH /api/v1/accounts/users/me`
- `GET/PATCH /api/v1/accounts/profile/me`
- `GET/POST /api/v1/classrooms/`
- `POST /api/v1/classrooms/join/`
- `GET /api/v1/classrooms/<id>/`

## Deployment Notes

- Procfile-based deployment is configured for migration, static collection, and Gunicorn serving.
- Production database migration to PostgreSQL is planned/recommended.

## Roadmap

- Resource upload endpoints for classrooms.
- In-app PDF viewer integration.
- Attendance management (daily, bulk, and mark-assignment style attendance).
- Enhanced classroom management actions (update/delete lifecycle improvements).

## Current Status

Gradus is actively evolving and already supports core internal mark evaluation workflows from authentication to grading and student performance visibility.

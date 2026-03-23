# Gradus API Documentation

**Base API URL:** `/api/v1/`

All endpoints (unless marked **Public**) require authentication. Depending on the setup, this is either a Session Cookie or an Authorization Header (`Authorization: Token <your_token>`).

---

## 1. Authentication & Accounts (`/api/v1/accounts/` & `/api/v1/auth-token/`)

### Auth Token (For mobile/SPA)
- `POST /api/v1/auth-token/login/` — **Public** | Returns `{ "token": "..." }` in exchange for `username` and `password`.
- `POST /api/v1/auth-token/logout/` — Invalidates the current token.

### Session Login (For traditional web)
- `POST /api/v1/accounts/login/` — **Public** | Logs in user via session.
- `POST /api/v1/accounts/logout/` — Logs out session user.

### Registration & Profiles
- `POST /api/v1/accounts/register/` — **Public** | Register a new user. Expects `username`, `email`, `password`, `confirm_password`, `first_name`, `last_name`, and `is_student` boolean. 
- `GET /api/v1/accounts/users/me` — Get current logged-in user details.
- `PUT / PATCH /api/v1/accounts/users/me` — Update user details (e.g. first/last name).
- `GET /api/v1/accounts/users/<username>` — View any user's public profile.
- `GET /api/v1/accounts/profile/me` — Get current user's role-specific profile (Student or Teacher fields).
- `PUT / PATCH /api/v1/accounts/profile/me` — Update role-specific profile fields (e.g. `roll_no`, `department`, `phone_number`).

### Password Reset Flow
1. `POST /api/v1/accounts/password-reset/request/` — **Public** | Expects `email`. Sends an OTP code to email.
2. `POST /api/v1/accounts/password-reset/verify/` — **Public** | Expects `email` and `otp`. Returns a `reset_token`.
3. `POST /api/v1/accounts/password-reset/confirm/` — **Public** | Expects `email`, `reset_token`, and `new_password`. Changes the password.

---

## 2. Classrooms (`/api/v1/classrooms/`)

- `GET /api/v1/classrooms/` — List classrooms (Teachers see created; Students see joined).
- `POST /api/v1/classrooms/` — **Teachers Only** | Create a new classroom. Expects `name` and `description`.
- `GET /api/v1/classrooms/<uuid>/` — Get classroom details (includes `invite_code`, list of students, list of resources).
- `POST /api/v1/classrooms/join/` — **Students Only** | Expects `invite_code`. Adds student to classroom.
- `POST /api/v1/classrooms/<uuid>/students/` — **Teachers Only** | Force-add a student manually. Expects `roll_no`.
- `GET /api/v1/classrooms/<uuid>/gradebook/` — View grade/performance payload for the classroom tasks.
- `GET /api/v1/classrooms/<uuid>/tasks/` — List all published tasks in a specific classroom.
- `POST /api/v1/classrooms/<uuid>/tasks/` — **Teachers Only** | Create a new task in this classroom.

---

## 3. Tasks & Records (`/api/v1/tasks/`)

- `GET /api/v1/tasks/<uuid>/` — Retrieve a specific task's details.
- `PUT / PATCH /api/v1/tasks/<uuid>/` — **Teachers Only** | Update a task.
- `DELETE /api/v1/tasks/<uuid>/` — **Teachers Only** | Delete a task.

### Task Records (Submissions & Grades)
- `GET /api/v1/tasks/<uuid>/submit/` — List records for this task (Teachers see all; Students see their own).
- `POST /api/v1/tasks/<uuid>/submit/` — **Students Only** | Submit work for **ONLINE tasks ONLY**. Needs `multipart/form-data` with `uploaded_file`.
- `PUT / PATCH /api/v1/tasks/records/<record_id>/update` — **Students Only** | Update an existing submission file (allowed only before deadline/evaluation).

### Grading & Evaluation (Teachers Only)
- `POST /api/v1/tasks/<uuid>/bulk-evaluate/` — Bulk evaluate **OFFLINE tasks ONLY** via CSV. Needs `multipart/form-data` with `file`. (Format: `Roll No, Marks, Feedback`).
- `POST /api/v1/tasks/<uuid>/evaluate-student/<student_id>/` — Manually evaluate a student directly (creates or updates the record). Expects `marks_obtained` and `feedback`.
- `PATCH /api/v1/tasks/records/<record_id>/evaluate/` — Evaluate or update marks for an existing task record. Expects `marks_obtained` and `feedback`.
- `GET /api/v1/tasks/records/<record_id>/` — View full record details (includes submission file, marks, and feedback).

---

## 4. Resources (`/api/v1/resources/`)

Used for attaching files to Classrooms or Tasks. Supports `multipart/form-data`.

- `GET /api/v1/resources/` — List resources. Filter with `?content_type=<model>&object_id=<uuid>`.
- `POST /api/v1/resources/` — Upload a resource. Expects `name`, `file`, `content_type`, `object_id`.
- `GET /api/v1/resources/<id>/` — Retrieve details (including file URL).
- `DELETE /api/v1/resources/<id>/` — Delete a resource.

---

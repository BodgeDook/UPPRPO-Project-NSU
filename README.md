# uMoive 
## Audio Video computer editor
UPPRPO project by NSU students (2nd year, 4th semester).
All dependencies are included. FFmpeg, RapidJSON


## Project structure

```
uMovie/
├── desktop-app/
│   ├─ main.py             # Entry point for the desktop application
│   ├─ models/              # “Pure” Python logic, no Qt imports
│   │   ├─ auth.py
│   │   ├─ project.py # Project, Timeline, Asset logic
│   │   ├─ timeline.py
│   │   └─ render.py  # The c++ redner wrapper
│   │
│   ├─ view/                # All our QMainWindow/QDialog subclasses
│   │   ├─ welcome.py       # WelcomeWindow (signals only)
│   │   ├─ editor.py        # EditorWindow (signals only)
│   │   ├─ settings.py      # SettingsDialog
│   │   └─ auth.py         # LoginDialog
│   │
│   ├─ controllers/         # Glue between models <-> views
│   │   ├─ app_controller.py    # Instantiates Welcome, Editor, Settings, Auth
│   │   └─ auth.py   # Handles register/login flows
│   │
│   ├─ widgets/             # Sub-components for the editor window
│   │   ├─ timeline.py
│   │   ├─ preview.py
│   │   └─ toolbox.py
│   │
│   ├─ render/             # (aka. "engine") C++ rendering logic & ffmpeg integration
│   ├─ tests/              # Desktop app-specific tests (e.g., integration/unit tests)
│   ├─ dev-cache/          # App caches for development
│   ├─ ui-venv/            # Recommended location for the ui environment
│   ├─ requirements.txt    # Python dependencies for the UI
│
├── server/
│   ├─ app/                # Backend application code (API, business logic, etc.)
│   ├─ registration/       # User registration/login module
│   ├─ tests/              # Server-side tests
│   ├─ Dockerfile          # Docker setup for the backend server
│   ├─ requirements.txt    # Python dependencies for the backend
│   ├─ main.py             # Server entry point
│
├── database/
│   ├─ schema.sql          # PostgreSQL database schema and seed data if applicable
│   ├─ Dockerfile          # Docker setup for the database
│
├── docker-compose.yml      # Multi-container Docker Compose setup
├── docs/                   # Project documentation (design docs, API docs, etc.)
├── .gitignore
├── .env-example
└── README.md
```

---

Possible alternative:

```
project-root/
│── desktop-app/
│   ├── src/                 # Python UI and logic (renamed from 'ui/')
│   │   ├── ui/              # PythonQt UI
│   │   ├── core/            # C++ Render Engine
│   │   ├── __init__.py      # Treat as a Python package
│   ├── tests/               # Unit tests for UI and core
│   ├── Dockerfile           # Docker setup for UI app
│   ├── pyproject.toml       # Modern dependency management (Poetry/Pipenv)
│   ├── requirements.txt     # (Optional, if not using Poetry)
│   ├── CMakeLists.txt       # CMake build system for C++ part
│   ├── main.py              # Entry point
│── server/
│   ├── src/                 # Backend source code
│   │   ├── app/
│   │   ├── __init__.py
│   ├── tests/               # Unit tests for server logic
│   ├── Dockerfile           # Docker setup for backend
│   ├── pyproject.toml       # Modern dependency management
│   ├── requirements.txt     # (Optional)
│   ├── main.py              # Server entry point
│── database/
│   ├── migrations/          # Directory for DB migrations (Alembic/Flyway)
│   ├── schema.sql           # PostgreSQL schema
│   ├── seed.sql             # Initial seed data
│   ├── Dockerfile           # Docker setup for PostgreSQL
│── scripts/                 # Utility scripts (setup, DB, deployment)
│── docker-compose.yml       # Compose file for multi-container setup
│── .gitignore
│── README.md
│── .pre-commit-config.yaml  # Pre-commit hooks (linting, formatting)
│── .github/workflows/       # CI/CD (GitHub Actions, if applicable)
│── docs/                    # Documentation
│   ├── api.md
│   ├── setup.md
│   ├── architecture.md
```

# 📚 Table of Contents

- [.env setting](#env-setting)
- [Launch variants](#launch-variant)
  - [Local](#local-testing)
  - [With docker](#docker-testing)
  - [With ready domen](#our-server-option)
- [SQL tables](#info-about-sql)
- [Password requrments](#password-requirments)
- [FastApi requests](#fastapi-requests)
- [HTTP Exceptions](#http-exceptions)

# Env setting
First of all you should create an *.env* file to work with your PostgreSQL database and Google account, from which confirmation codes will be sent.
There should be such constance:
```
EMAIL_SENDER=
EMAIL_PASSWORD=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DATABASE=
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

EMAIL_PASSWORD - it is the app password of the Google account from which the messages will be sent.
You can read it in detail [here.](https://support.google.com/mail/answer/185833?hl=en&ref_topic=3394217&sjid=5235200406851987490-EU)

---
# Launch variant:
- local testing
- creating server part in docker by yourself 
- reling by us test the application for the first time using a default server with our domain.
---
## Local Testing
**Setting virtual env:**
```shell
root/server/registration/$ pip install -r requirements.txt
```
**Launchin FastApi app:**
```
uvicorn main:app --reload
```
**Launching UI:**
After all you could start testing our app: 
```shell
root/desktop-app/$ python3 main.py
```
---

## Docker testing
**Launching server:**
If you want to test app with docker containers just follow this comand:
```
root/server/registration/$ docker-compose up --build
```
_make sure that docker daemon is running_

**Launching UI:**
After all you could start testing our app: 
```shell
root/desktop-app/$ python3 main.py
```
---

## Our server option:
**just type:**
```shell
root/desktop-app/$ python3 main.py
```
---
Done! You launched Umovie video editor!
---
## info about SQL

**users table**

| Column       | Type                     | Nullable | Default |
|--------------|--------------------------|----------|---------|
| email        | `character varying(255)` | not null | -       |
| password     | `character varying(255)` | not null | -       |
| balance      | `numeric(10,2)`          | not null | `0.00`  |
| is_logged_in | `boolean`                | -        | `false` |
```
CREATE TABLE users (
    email VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_logged_in BOOLEAN DEFAULT FALSE
);
```

**veification_codes table**

| Column     | Type                          | Nullable | Default             |
|------------|-------------------------------|----------|---------------------|
| email      | `text`                        | not null | -                   |
| code       | `text`                        | not null | -                   |
| created_at | `timestamp without time zone` | -        | `CURRENT_TIMESTAMP` |
| is_used    | `boolean`                     | -        | `false`             |
```
CREATE TABLE verification_codes (
    email TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);
```

## password requirments:
- len > 8
- password should contain at least 1: lower letter, upper letter, special symbol


# FastApi requests

- registration
  ```
  curl -X 'POST' 'http://127.0.0.1:8000/user_registration?email=<email>&password=<password>' -H 'accept: application/json'
  ```
- login
  ```
  curl -X 'POST' 'http://127.0.0.1:8000/user_login?email=<email>&password=<password>' -H 'accept: application/json'
  ```
- logout
  ```
  curl "http://127.0.0.1:8000/user_logout?email=<email>"
  ```
- change password:
  ```
  curl -X 'POST' 'http://127.0.0.1:8000/user_change_passwords?email=<email>&password=<password>' -H 'accept: application/json'
  ```
- update balance (optionally)
  ```
  curl "http://127.0.0.1:8000/update_balance?email=<user_email>&amount=<some_float_val>"
  ```
- save the users table in json
  ```
  curl "http://127.0.0.1:8000/get_users_db"
  ```

- send code to email
  ```
  curl -X POST "http://127.0.0.1:8000/send-code/" -H "Content-Type: application/json" -d '{"email": "<email>"}'
  ```
- compare the user's code with the code from the verification_codes table
  ```
  curl -X POST "http://127.0.0.1:8000/check-code" -H "Content-Type: application/json" -d '{"email": "<email>", "user_code": "<code>"}'
  ```
- save the verification_codes table in json
  ```
  curl "http://127.0.0.1:8000/get_codes_db" 
  ```

# HTTP Exceptions
```
200 -- OK
400 -- Bad Request
401 -- Unauthorized
404 -- Not Found
409 -- Conflict With Server
422 -- Unprocessable Content
500 -- Internal Server Error
```

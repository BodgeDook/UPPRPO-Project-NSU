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
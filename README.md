# uMoive 
## Audio Video computer editor
UPPRPO project by NSU students (2nd year, 4th semester).
All dependencies are included. FFmpeg, RapidJSON


## Project structure options

```
project-root/
│── desktop-app/
│   ├── ui/                  # PythonQt UI
│   ├── core/                # C++ Render
│   ├── Dockerfile           # Docker setup for UI app
│   ├── requirements.txt     # Python dependencies
│   ├── main.py              # Entry point
│── server/
│   ├── app/
│   ├── Dockerfile           # Docker setup for backend
│   ├── requirements.txt     # Python dependencies
│   ├── main.py              # Server entry point
│── database/
│   ├── schema.sql           # PostgreSQL schema
│   ├── Dockerfile           # Docker setup for PostgreSQL
│── docker-compose.yml       # Compose file for multi-container setup
│── .gitignore
│── README.md
```

```
project-root/
├── desktop-app/
│   ├── ui/                  # Python/Qt UI code
│   ├── engine/              # C++ rendering logic & ffmpeg integration
│   ├── tests/               # Desktop app-specific tests (e.g., integration/unit tests)
│   ├── Dockerfile           # Docker setup for the desktop app (if needed in the future)
│   ├── requirements.txt     # Python dependencies for the UI
│   ├── main.py              # Entry point for the desktop application
│
├── server/
│   ├── app/                 # Backend application code (API, business logic, etc.)
│   ├── tests/               # Server-side tests
│   ├── Dockerfile           # Docker setup for the backend server
│   ├── requirements.txt     # Python dependencies for the backend
│   ├── main.py              # Server entry point
│
├── database/
│   ├── schema.sql           # PostgreSQL database schema and seed data if applicable
│   ├── Dockerfile           # Docker setup for the database
│
├── docker-compose.yml       # Multi-container Docker Compose setup
├── docs/                    # Project documentation (design docs, API docs, etc.)
├── .gitignore
└── README.md
```


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
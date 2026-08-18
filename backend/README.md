# Women Safety Risk-Zone Prediction System — Backend Foundation (Phase 1)

## 📌 Project Purpose
This repository houses the core FastAPI backend for the **Women Safety Risk-Zone Prediction System** (`SafeHer`). Phase 1 establishes a modular, secure, and production-grade foundation including environment configuration, database session handling, Redis integration, Celery background worker setup, structured logging, centralized exception handling, and automated health checks.

---

## 🏗️ Architecture & Project Structure
The backend follows a modular, decoupled architecture:

```
backend/
├── app/
│   ├── main.py                # FastAPI Application Factory & Exception Handlers
│   ├── api/
│   │   └── v1/                # Version 1 Routers (/api/v1/health)
│   ├── core/                  # Config, Logging, Exceptions, Security
│   ├── database/              # SQLAlchemy 2.x Engine, Session & Base
│   ├── services/              # Redis Client & External Services
│   ├── workers/               # Celery Worker Configuration & Health Task
│   ├── models/                # Database Models (Phase 2)
│   ├── schemas/               # Pydantic Request/Response Schemas
│   └── repositories/          # Data Access Layer
├── alembic/                   # Database Migrations
├── tests/                     # Pytest Test Suite
├── Dockerfile                 # Container image specification
├── docker-compose.yml         # Local infrastructure (Backend, Postgres, Redis)
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 📋 Requirements
* **Python**: `3.11+`
* **PostgreSQL**: `15+`
* **Redis**: `7+`
* **Docker & Docker Compose** (Optional for containerized setup)

---

## ⚙️ Environment Setup

1. **Clone the repository & enter backend directory:**
   ```bash
   git clone https://github.com/pranav-3010/safeher.git
   cd safeher/backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy the example environment configuration file to `.env`:
   ```bash
   cp .env.example .env
   ```

---

## 🐳 Docker Setup

To start all backend infrastructure services (PostgreSQL, Redis, FastAPI Backend) in containers:

```bash
docker-compose up --build -d
```

To view running containers and logs:
```bash
docker-compose ps
docker-compose logs -f backend
```

To stop containers:
```bash
docker-compose down
```

---

## 🚀 Running FastAPI Locally

Ensure PostgreSQL and Redis are running locally or via Docker, then execute:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Interactive API Documentation (Swagger):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* **ReDoc Documentation:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

## ⚡ Running Celery Worker

In a separate terminal window with the virtual environment activated:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

---

## 🧪 Running Automated Tests

Run the pytest suite to verify application startup, configuration validation, database reachability, Redis ping, and Celery initialization:

```bash
pytest -v
```

---

## 🏥 Health Check Endpoint

### `GET /api/v1/health`

Verifies infrastructure status across all underlying dependencies.

**Sample Healthy Response (HTTP 200):**
```json
{
    "status": "healthy",
    "service": "women-safety-backend",
    "environment": "development",
    "services": {
        "api": "ok",
        "database": "ok",
        "redis": "ok",
        "celery": "configured"
    }
}
```

**Sample Degraded Response (HTTP 503):**
```json
{
    "status": "degraded",
    "service": "women-safety-backend",
    "environment": "development",
    "services": {
        "api": "ok",
        "database": "unreachable",
        "redis": "ok",
        "celery": "configured"
    }
}
```

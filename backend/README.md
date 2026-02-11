# ADO Readiness Backend

FastAPI backend for the ADO Migration Readiness Analyzer.

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .
pip install -e ../  # Install main package
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/config` | Get configuration status |
| POST | `/api/config` | Save configuration |
| DELETE | `/api/config` | Delete configuration |
| GET | `/api/test-connection` | Test ADO connection |
| POST | `/api/scan` | Start organization scan |
| GET | `/api/scan/status` | Get scan progress |
| GET | `/api/scan/results` | Get scan results |
| GET | `/api/repos` | List repos for migration |
| POST | `/api/migrate` | Start repo migration |
| GET | `/api/migrate/status` | Get migration progress |
| WS | `/ws/progress` | WebSocket for real-time updates |

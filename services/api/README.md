# API

FastAPI app in `ngreen_api`. Run from the repository root:

```powershell
.\.venv\Scripts\python -m uvicorn ngreen_api.main:app --app-dir services/api --reload --port 8000
```

`GET /health` is public. Everything under `/api/v1` except `POST /api/v1/auth/demo/login` requires a bearer token. DEMO staff are seeded on startup when `DEMO_AUTH_ENABLED=true`.

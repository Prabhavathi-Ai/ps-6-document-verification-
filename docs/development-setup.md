# Development setup

## Backend

### Install dependencies

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Start the API server

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\backend"
set PYTHONPATH=.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run backend tests

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\backend"
set PYTHONPATH=.
python -m pytest app/tests/test_health.py -q
```

## Frontend

### Install dependencies

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\frontend"
npm install
```

### Start the dev server

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\frontend"
npm run dev -- --host 0.0.0.0
```

### Run frontend build

```powershell
cd "C:\Users\ELCOT\Downloads\ps-6-document-verification-\frontend"
npm run build
```

### Run frontend tests

This initial phase does not yet include a dedicated frontend unit test runner; the project uses the production build as the primary frontend verification step.

## Environment variables

Create a local .env file in the repository root using the values from .env.example.

## Notes

- The backend uses environment-driven configuration.
- CORS is configured for the local React dev server.
- Sensitive data and secrets are never committed.

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
python -m pytest app/tests -q
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

Phase 2 database and storage settings include:

- `DATABASE_URL=sqlite:///./data/veridoc.db`
- `STORAGE_ROOT=./storage`
- `MAX_UPLOAD_SIZE_MB=20`

The application creates the SQLite parent directory, database tables, and local storage directories when needed. Database files and original files are excluded from Git.

## Document API

- `POST /api/v1/documents` accepts PDF, PNG, JPG, and JPEG uploads.
- `GET /api/v1/documents?page=1&page_size=20` lists stored metadata.
- `GET /api/v1/documents/{document_id}` returns metadata for one document.
- `GET /api/v1/documents/{document_id}/file` retrieves the preserved original.
- `GET /docs` exposes the generated Swagger UI.

Uploaded documents are stored with generated internal filenames under `storage/originals/`. The original filename remains metadata only. Phase 2 does not process uploaded content.

## Notes

- The backend uses environment-driven configuration.
- CORS is configured for the local React dev server.
- Sensitive data and secrets are never committed.

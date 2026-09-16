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
- `MAX_PAGE_SIZE=100`

The application creates the SQLite parent directory, database tables, and local storage directories when needed. Database files and original files are excluded from Git.

## Document API

- `POST /api/v1/documents` accepts PDF, PNG, JPG, and JPEG uploads.
- `GET /api/v1/documents?page=1&page_size=20` lists stored metadata.
- `GET /api/v1/documents/{document_id}` returns metadata for one document.
- `GET /api/v1/documents/{document_id}/file` retrieves the preserved original.
- `GET /docs` exposes the generated Swagger UI.

Uploaded documents are stored with generated internal filenames under `storage/originals/`. The original filename remains metadata only. Phase 2 does not process uploaded content.

## Phase 4 ingestion hardening

The upload boundary validates filename safety, extension, declared MIME type, file signatures, image readability, empty files, and the configured size limit before storage or database insertion. PDFs require a `%PDF-` signature; PNG/JPEG uploads require their expected signatures and successful image decoding.

Originals are written exclusively under `storage/originals/` using generated UUID filenames. Storage writes use exclusive creation and clean up partial files on failure. Database failures roll back and remove a newly stored original. No upload is marked successful unless both storage and metadata persistence succeed.

Upload failures use stable error codes such as `EMPTY_FILE`, `FILE_TOO_LARGE`, `UNSUPPORTED_FILE_TYPE`, `INVALID_FILE_CONTENT`, `MIME_TYPE_MISMATCH`, `INVALID_FILENAME`, `STORAGE_ERROR`, and `DATABASE_ERROR`. The API never returns internal filesystem paths or stack traces.

## Notes

- The backend uses environment-driven configuration.
- CORS is configured for the local React dev server.
- Sensitive data and secrets are never committed.

# VeriDoc AI

## Project status

This repository is now in Phase 4 document-ingestion hardening mode. The project has the approved Phase 2 upload foundation, Phase 3 synthetic benchmark tooling, and a reusable validation boundary for signatures, MIME/content consistency, image readability, filename safety, size limits, hashing, and failure cleanup. No OCR, ELA, duplicate detection, fraud scoring, or document-analysis services have been implemented.

## Objective

Build an AI-assisted document verification and fraud-detection platform that can:

- extract structured fields from scanned or photographed documents via OCR,
- validate field consistency and document metadata,
- detect exact and near-duplicate documents,
- identify semantic similarity and risk signals,
- perform forensic analysis using ELA and image anomaly techniques,
- provide explainable suspicious-region overlays and risk scoring,
- support both single-document and bulk processing,
- measure performance on benchmark datasets.

## Phase 4 scope

This phase hardens the upload boundary without adding processing:

- extension, MIME, signature, and image-readability validation,
- safe filename and path traversal rejection,
- configurable upload and pagination limits,
- structured safe upload errors,
- immutable exclusive original storage,
- database/storage failure cleanup,
- byte-level SHA-256 integrity tests,
- accessible upload loading, success, and error states.

No OCR, PaddleOCR, field extraction, logical validation, duplicate detection algorithms, pHash, embeddings, Qdrant, ELA, pixel/noise analysis, fraud scoring, risk scoring, heatmaps, batch processing, or advanced document verification is included in this phase.

## Repository structure

- backend/
- frontend/
- docs/
- datasets/
- benchmarks/
- reports/

## Backend setup

From the repository root:

1. cd backend
2. python -m venv .venv
3. .\.venv\Scripts\Activate.ps1
4. python -m pip install -r requirements.txt
5. set PYTHONPATH=. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

## Frontend setup

From the repository root:

1. cd frontend
2. npm install
3. npm run dev -- --host 0.0.0.0

## Test commands

Backend:

- cd backend
- set PYTHONPATH=. && python -m pytest app/tests -q

Dataset framework:

- python scripts/generate_synthetic_benchmark.py --seed 42
- python scripts/validate_dataset.py
- python scripts/dataset_inventory.py
- python -m pytest scripts/test_dataset_framework.py -q

Frontend:

- cd frontend
- npm run build
- npm run test -- --run

## Documentation set

- [docs/architecture.md](docs/architecture.md)
- [docs/data-model.md](docs/data-model.md)
- [docs/dataset-strategy.md](docs/dataset-strategy.md)
- [docs/benchmark-strategy.md](docs/benchmark-strategy.md)
- [docs/development-roadmap.md](docs/development-roadmap.md)
- [docs/forensic-analysis-principles.md](docs/forensic-analysis-principles.md)
- [docs/development-setup.md](docs/development-setup.md)

## Phase 1 completion gate

Phase 1 is complete only after the backend and frontend foundations are both verified to run, the health API is tested, the build and test commands are documented, and the human stakeholder approves the foundation before Phase 2 begins.

"PHASE 1 COMPLETE — AWAITING HUMAN APPROVAL"

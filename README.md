# VeriDoc AI

## Project status

This repository is currently in Phase 0 audit mode. No application implementation, frontend, backend, API, or dataset code was present in the checked-out working tree, so the project is being defined from a clean architectural baseline rather than replacing an existing implementation.

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

## Phase 0 scope

The current work is limited to repository audit, architecture definition, data model planning, dataset and benchmark strategy, forensic terminology, development roadmap, and verification of the project baseline. No production implementation is started in this phase.

## Current repository findings

- automation baseline is not yet established,
- no frontend application files exist in the working tree,
- no backend service or Python project files exist in the working tree,
- no package manifests or dependency files are present,
- no database configuration or API routes are present,
- no tests are present yet,
- no dataset assets are checked into the repository.

## Target technology direction

The project is intended to follow a Python FastAPI backend with a React frontend, plus OpenCV and OCR tooling for document analysis. Qdrant and a relational metadata store are intended for duplicate-search and metadata tracking, while uploaded files and derived artifacts will be stored in object/file storage on the deployment platform.

## Documentation set

- [docs/architecture.md](docs/architecture.md)
- [docs/data-model.md](docs/data-model.md)
- [docs/dataset-strategy.md](docs/dataset-strategy.md)
- [docs/benchmark-strategy.md](docs/benchmark-strategy.md)
- [docs/development-roadmap.md](docs/development-roadmap.md)
- [docs/forensic-analysis-principles.md](docs/forensic-analysis-principles.md)

## Repository structure target

- backend/
- frontend/
- datasets/
- docs/
- scripts/
- tests/
- benchmarks/
- reports/

## Phase 0 completion gate

Phase 0 is considered complete only after the repository has been audited, the architecture and benchmarks are documented, the data model is defined, and the findings are approved by the human stakeholder before moving to Phase 1.

"PHASE 0 COMPLETE — AWAITING HUMAN APPROVAL"

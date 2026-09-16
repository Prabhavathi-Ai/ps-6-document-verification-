# Development roadmap

## Phase 0

Goal:
- audit repository, establish architecture, document the data model, define benchmark strategy, and capture risks before implementation.

Outputs:
- audit report,
- architecture documentation,
- data model and forensic principles,
- datasets and benchmark strategy,
- roadmap and risk register,
- approval gate before starting implementation.

## Phase 1

Goal:
- define the project skeleton and core runtime contracts.

Expected work:
- initialize backend project structure,
- initialize frontend project structure,
- define API contracts and schemas,
- add database models and migration planning,
- define document processing job queue contracts,
- add placeholder tests and build verification.

## Phase 2

Goal:
- build ingestion and preprocessing pipeline.

Expected work:
- upload handling,
- file validation,
- storage integration,
- preprocessing and normalization,
- document quality checks,
- intermediate artifact generation.

## Phase 3

Goal:
- establish reproducible dataset acquisition and benchmark setup.

Expected work:
- dataset source registry and honest access/licensing status,
- synthetic benchmark generation,
- ground-truth metadata and mask relationships,
- leakage-safe source-group splits,
- dataset validation and inventory tooling.

OCR and extraction are deferred to a later approved phase.

## Phase 4

Goal:
- harden document ingestion and upload validation.

Expected work:
- content signatures and MIME consistency,
- image readability and malformed-file rejection,
- secure filename and immutable original handling,
- structured upload errors and failure cleanup,
- byte-level integrity and ingestion security tests.

OCR and extraction remain deferred to a later approved phase.

## Phase 5

Goal:
- implement deterministic image preprocessing.

Expected work:
- bounded image decoding and PDF rendering,
- EXIF orientation handling,
- RGB PNG analysis representations,
- aspect-ratio-preserving resolution normalization,
- derived page metadata and original-integrity tests.

OCR and extraction remain deferred to a later approved phase.

## Phase 6

Goal:
- implement OCR and extraction workflow.

Expected work:
- OCR engine integration,
- structured field extraction,
- confidence scoring,
- output normalization,
- extraction validation and review UI.

## Phase 7

Goal:
- implement validation and duplicate detection.

Expected work:
- rule-based field validation,
- duplicate hashing and vector comparison,
- similarity scoring,
- duplicate category assignment.

## Phase 8

Goal:
- implement forensic analysis and explainability.

Expected work:
- ELA computation,
- anomaly detection,
- suspicious-region masks,
- overlay rendering,
- evidence explanations and review views.

## Phase 9

Goal:
- integrate risk scoring and final dashboard.

Expected work:
- risk model assembly,
- model configuration,
- summary dashboards,
- bulk review workflows,
- reporting and export.

## Phase 10

Goal:
- dataset benchmarking and evaluation.

Expected work:
- benchmark dataset setup,
- evaluation scripts,
- metrics reporting,
- visual comparison of evidence signals,
- threshold tuning and validation.

## Phase 11

Goal:
- system hardening and deployment readiness.

Expected work:
- production configuration,
- observability,
- monitoring,
- deployment pipeline,
- security review,
- performance tuning.

## Minimum commit expectation

The project target is a minimum of 50 meaningful Git commits across all phases, with only meaningful changes committed after validation.

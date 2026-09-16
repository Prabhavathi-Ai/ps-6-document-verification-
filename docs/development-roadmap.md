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
- implement OCR and extraction workflow.

Expected work:
- OCR engine integration,
- structured field extraction,
- confidence scoring,
- output normalization,
- extraction validation and review UI.

## Phase 4

Goal:
- implement validation and duplicate detection.

Expected work:
- rule-based field validation,
- duplicate hashing and vector comparison,
- similarity scoring,
- duplicate category assignment.

## Phase 5

Goal:
- implement forensic analysis and explainability.

Expected work:
- ELA computation,
- anomaly detection,
- suspicious-region masks,
- overlay rendering,
- evidence explanations and review views.

## Phase 6

Goal:
- integrate risk scoring and final dashboard.

Expected work:
- risk model assembly,
- model configuration,
- summary dashboards,
- bulk review workflows,
- reporting and export.

## Phase 7

Goal:
- dataset benchmarking and evaluation.

Expected work:
- benchmark dataset setup,
- evaluation scripts,
- metrics reporting,
- visual comparison of evidence signals,
- threshold tuning and validation.

## Phase 8

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

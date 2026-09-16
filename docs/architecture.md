# Architecture

## 1. Purpose

This project will provide an AI-assisted document verification pipeline that can inspect submitted document images, extract fields, validate consistency, detect duplicates, perform forensic analysis, and compute evidence-based risk scores.

## 2. System context

The high-level flow is:

Frontend
↓
API layer
↓
Document processing pipeline
↓
Preprocessing
↓
OCR
↓
Structured extraction
↓
Validation
↓
Duplicate detection
↓
Forensic analysis
↓
Risk engine
↓
Explainability layer
↓
Database / vector database / storage

## 3. Architectural principles

- Each stage must be independently testable.
- No single forensic signal is treated as definitive proof of fraud.
- Processing is event-driven and status-aware.
- Validation and duplicate checks operate from normalized document metadata.
- Explainability outputs must be tied to evidence, not generic confidence labels.
- Benchmarking must be separated from production runtime pipelines.

## 4. Layered architecture

### 4.1 Frontend

The frontend will provide a responsive document upload workflow, review pages, anomaly overlays, and result summaries. The intended stack is React with a responsive/mobile-first layout.

Responsibilities:

- upload and queue document jobs,
- preview images and derived overlays,
- show OCR-extracted fields for review,
- show validation inconsistencies and duplicate matches,
- render suspicious regions using HTML5 Canvas,
- display a risk summary with evidence explanations,
- support bulk upload and benchmarking workflows.

### 4.2 API layer

The API layer is intended to be Python-based and may use FastAPI for endpoints, background job orchestration, and schema validation.

Responsibilities:

- accept uploads and create processing jobs,
- coordinate pipeline execution,
- return status updates and result objects,
- expose document-level and batch-level analysis APIs,
- expose benchmark and evaluation APIs,
- manage auth/session requirements if later introduced.

### 4.3 Processing orchestration

The processing pipeline includes the following stages:

1. ingestion
2. preprocessing
3. OCR
4. extraction
5. validation
6. duplicate detection
7. forensic analysis
8. scoring
9. visualization
10. evaluation

Each stage should emit structured artifacts and status metadata so tasks can be resumed or retried independently.

### 4.4 Ingestion

- accept document image files,
- validate format and size,
- validate filename, declared MIME, file signature, and image readability before persistence,
- create document metadata records,
- persist original files in object storage,
- generate processing job records,
- route into preprocessing pipeline.

Phase 4 ingestion hardening keeps the original upload immutable. Generated storage names are resolved beneath the originals root, writes are exclusive, and a database failure rolls back metadata and removes the new original. SHA-256 is calculated from the exact uploaded bytes. Validation failures do not create document records.

### 4.5 Preprocessing

- normalize image orientation,
- convert color spaces as needed,
- deskew and denoise when appropriate,
- detect page boundaries and crop if necessary,
- generate intermediate images for OCR and forensic analysis,
- record preprocessing metadata and tolerances.

### 4.6 OCR

- run OCR on preprocessed images,
- produce text blocks, confidence scores, and bounding boxes,
- keep raw OCR output separate from normalized fields,
- preserve region-level evidence for explainability.

### 4.7 Structured extraction

- map OCR tokens and spatial regions into document field schemas,
- support invoice, receipt, ID-card, certificate, form, and generic document types,
- produce extracted field objects with confidence and source regions,
- maintain a trace between field values and OCR evidence.

### 4.8 Validation

- compare extracted fields against expected rules,
- cross-check values across fields within the same document,
- flag format issues, missing values, and contradictory values,
- identify validation inconsistencies as evidence instead of proof.

### 4.9 Duplicate detection

- compare documents using exact and near-duplicate detection,
- compute hash-based comparisons and perceptual similarity,
- compare text embeddings and layout similarity when available,
- use vector search for candidate matching,
- keep duplicate similarity separate from tampering evidence.

### 4.10 Forensic analysis

- compute ELA metrics for suspicious regions,
- extract pixel/noise features,
- analyze spatial and layout anomalies,
- estimate document tampering likelihood while preserving uncertainty,
- generate suspicious-region masks and associated evidence.

### 4.11 Risk engine

- combine validation, duplicate, forensic, and document metadata signals,
- assign calibrated risk indicator scores,
- report confidence and reasoning categories,
- separate low-confidence anomalies from actionable findings.

### 4.12 Explainability and visualization

- render suspicious regions on the document canvas,
- show duplicate similarity highlights,
- display field-level validation warnings,
- connect each warning to specific evidence and confidence.

### 4.13 Database and storage

- relational database for application metadata,
- object/file storage for uploaded originals and derived artifacts,
- vector database for similarity search,
- structured benchmark metadata for offline evaluation.

## 5. Document lifecycle

Recommended states:

UPLOADED
→ PREPROCESSING
→ OCR_PROCESSING
→ EXTRACTION
→ VALIDATION
→ DUPLICATE_CHECK
→ FORENSIC_ANALYSIS
→ RISK_ANALYSIS
→ COMPLETED

Additional terminal states:

- FAILED
- CANCELLED
- REQUIRES_REVIEW

State transition rules:

- UPLOADED: the file is accepted and a processing job is created.
- PREPROCESSING: image normalization and validation are in progress.
- OCR_PROCESSING: OCR is running or awaiting worker execution.
- EXTRACTION: field-level extraction is being performed.
- VALIDATION: consistency checks and rule validation are running.
- DUPLICATE_CHECK: same-document or duplicate-document comparison is running.
- FORENSIC_ANALYSIS: ELA and anomaly analysis are running.
- RISK_ANALYSIS: risk score and explanation synthesis is running.
- COMPLETED: all planned stages complete successfully.
- FAILED: a stage fails and the job cannot continue without intervention.
- CANCELLED: processing was stopped by user/system action.
- REQUIRES_REVIEW: processing succeeded but findings need human review.

## 6. Testing isolation

The architecture should support unit tests and integration tests at each stage:

- preprocessing tests for rotation, crop, and normalization,
- OCR tests for extraction quality and error boundaries,
- validation tests for rule compliance,
- duplicate detection tests on exact and near-duplicate groups,
- forensic tests on ELA metrics and annotation alignment,
- scoring tests on risk-output consistency,
- API tests on job lifecycle and response payloads.

## 7. Risks and constraints

- ELA is not a standalone fraud detector.
- Duplicate artifacts may imitate tampering evidence unless distinguished by category.
- OCR and extraction quality are sensitive to document quality and imaging conditions.
- Data privacy requires careful handling of any uploaded documents and benchmark sets.

## 8. Phase 0 outcome

The goal of Phase 0 is to define the architecture and guardrails. Production implementation begins only after human approval.

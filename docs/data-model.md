# Data model

## 1. Design goals

The initial model should preserve evidence provenance, document identity, and pipeline execution history without over-engineering the schema too early. Each object should support traceability from the original upload to extracted fields, forensic findings, and final risk scores.

## 2. Core entities

### Document

Purpose:
- represents the uploaded document instance and its known metadata.

Key fields:
- id: UUID or surrogate primary key
- external_id: optional business identifier
- file_name
- file_path or storage key
- mime_type
- file_size_bytes
- sha256_hash
- document_type
- source
- status
- created_at
- updated_at
- deleted_at (optional)

Relationships:
- one document has many processing jobs
- one document may have many extracted fields
- one document may produce multiple forensic results and duplicate comparisons

Identifiers:
- document id as primary key
- hash for integrity checking and deduplication

Status:
- UPLOADED, PROCESSING, COMPLETED, FAILED, REQUIRES_REVIEW, CANCELLED

Error handling:
- store error_code, error_message, and the failing stage for traceability.

### ProcessingJob

Purpose:
- tracks a single pipeline execution for a document or batch task.

Key fields:
- id
- document_id
- job_type
- status
- stage_name
- queue_name
- requested_at
- started_at
- finished_at
- retries
- worker_id
- error_code
- error_message

Relationships:
- belongs to one document
- may produce many OCR results, duplicate checks, and forensic results

Identifiers:
- job id primary key
- document id foreign key

Status:
- queued, running, failed, cancelled, completed

Error handling:
- record stage-level failure, retry count, and delayed retries.

### OCRResult

Purpose:
- stores OCR outputs and their provenance.

Key fields:
- id
- processing_job_id
- document_id
- engine_name
- language
- raw_text
- normalized_text
- confidence_score
- page_index
- created_at

Relationships:
- belongs to one processing job
- can be linked to many extracted fields

Identifiers:
- OCR result id primary key

Status:
- successful or failed per OCR run

Error handling:
- preserve raw OCR text even when confidence is low;
- annotate missing OCR data as partial

### ExtractedField

Purpose:
- captures a normalized field value extracted from OCR or document structure.

Key fields:
- id
- document_id
- processing_job_id
- field_name
- field_value
- normalized_value
- confidence
- source_region
- page_index
- created_at
- updated_at

Relationships:
- belongs to one document and optionally one OCR result
- can feed validation results and risk calculations

Identifiers:
- extracted field id primary key

Status:
- extracted, reviewed, rejected, invalid

Error handling:
- keep raw OCR evidence, confidence, and parsing exceptions.

### ValidationResult

Purpose:
- records rule-based or learned validation issues.

Key fields:
- id
- document_id
- field_id (nullable)
- validation_rule
- status
- severity
- message
- observed_value
- expected_value
- created_at

Relationships:
- may point to one extracted field or a document-level rule

Identifiers:
- result id primary key

Status:
- PASS, FAIL, WARNING, UNKNOWN

Error handling:
- do not collapse all issues into a single boolean; retain details and severity.

### DuplicateResult

Purpose:
- records similarity with other documents or a candidate set.

Key fields:
- id
- document_id
- matched_document_id
- duplicate_category
- similarity_score
- hash_match
- perceptual_hash_distance
- embedding_similarity
- layout_similarity
- created_at
- status

Relationships:
- compares one document against another document
- may be grouped by exact, near, or synthetic duplicate class

Identifiers:
- result id primary key

Status:
- pending, candidate, confirmed, rejected

Error handling:
- keep comparison metadata; do not assume a duplicate is fraud.

### ForensicResult

Purpose:
- records forensic signals such as ELA or anomaly metrics.

Key fields:
- id
- document_id
- processing_job_id
- signal_type
- signal_name
- metric_value
- suspicious_region_mask_path
- region_count
- largest_region_area
- mean_error
- max_error
- created_at
- status

Relationships:
- relates to one document and job
- may produce multiple forensic artifacts

Identifiers:
- forensic result id primary key

Status:
- computed, reviewed, rejected

Error handling:
- always keep the numerical metrics even if the final interpretation remains uncertain.

### RiskResult

Purpose:
- stores the final risk score and explanation summary for a document.

Key fields:
- id
- document_id
- processing_job_id
- overall_risk_score
- risk_level
- explanation_summary
- confidence
- created_at

Relationships:
- belongs to the final document risk assessment
- can aggregate validation, duplicate, and forensic evidence

Identifiers:
- result id primary key

Status:
- active, archived, superseded

Error handling:
- retain evidence links rather than only the final number.

### DatasetDocument

Purpose:
- tracks benchmark documents used for evaluation.

Key fields:
- id
- dataset_name
- source_identifier
- document_type
- authenticity_label
- tamper_label
- ground_truth_mask_path
- metadata_json
- created_at

Relationships:
- belongs to a dataset collection
- may be linked to benchmark results

Identifiers:
- id primary key

Status:
- published, validated, excluded

Error handling:
- license and annotation provenance must be preserved.

### BenchmarkResult

Purpose:
- stores evaluation outputs for a benchmark run against a dataset.

Key fields:
- id
- benchmark_name
- dataset_name
- model_version
- category
- accuracy
- precision
- recall
- f1_score
- roc_auc
- execution_time_seconds
- created_at

Relationships:
- aggregates many evaluated document predictions

Identifiers:
- benchmark result id primary key

Status:
- queued, running, completed, failed

Error handling:
- keep dataset versioning and configuration snapshots.

## 3. Relationships summary

Document
- 1:N ProcessingJob
- 1:N ExtractedField
- 1:N ValidationResult
- 1:N DuplicateResult
- 1:N ForensicResult
- 1:N RiskResult

ProcessingJob
- N:1 Document
- 1:N OCRResult
- 1:N ForensicResult

DatasetDocument
- 1:N BenchmarkResult (conceptually or through dataset evaluation metadata)

## 4. Timestamps and auditability

The Phase 4 ingestion contract keeps `Document.status` at `UPLOADED` after accepted storage. Invalid input never creates a successful document record. The stored `sha256_hash` represents the original uploaded bytes, while the storage key remains internal and is not exposed by public metadata responses.

Every major entity should record:
- created_at
- updated_at
- completed_at (when applicable)
- archived_at (if needed)

This preserves a clear chain of evidence and supports debugging of pipeline issues.

## 5. Phase 0 scope

This model is intended as a documentation baseline only. It does not require immediate database migrations or table implementation.

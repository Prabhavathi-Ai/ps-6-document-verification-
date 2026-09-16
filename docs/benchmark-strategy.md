# Benchmark strategy

## 1. Benchmark categories

The future evaluation framework must distinguish the following document categories:

A. Genuine Original
- authentic document with no duplication or tampering evidence

B. Exact Duplicate
- byte-identical or near-identical repeated copy of the same original

C. Near Duplicate
Examples:
- resized copy
- JPEG recompressed copy
- renamed copy
- screenshot or resaved copy
- slight rotation
- minor crop

D. Tampered Document
Examples:
- amount modification
- date modification
- text replacement
- copied region
- inserted region
- deleted region
- synthetic or AI-manipulated content where available

E. Tampered + Duplicate
- a document that was tampered and then resized, compressed, or copied later

This last class is important because duplication operations can create false positive forensic signals unless the model explicitly distinguishes them.

## 2. Benchmark objectives

- test OCR extraction quality,
- test duplicate detection and similarity ranking,
- evaluate forensic anomaly detection,
- evaluate tamper localization quality,
- separate pure duplication similarity from actual manipulation evidence.

## 3. ELA benchmark design

The future ELA benchmark should compare:

Original
vs
Exact Duplicate
vs
Near Duplicate
vs
Tampered

For each document, compute measurable quantities such as:

- mean ELA error
- maximum ELA error
- high-error pixel percentage
- suspicious-region count
- largest suspicious-region area
- connected-component statistics

Where ground-truth tamper masks are available, compare the model-predicted suspicious regions against the true masks.

## 4. ELA interpretation rules

ELA can be affected by:

- JPEG compression,
- image resizing,
- screenshots,
- repeated saving,
- different compression quality,
- image format,
- scanning,
- document source.

Therefore, ELA must not be treated as a standalone fraud detector. It should be interpreted as one signal among multiple evidence sources.

## 5. Duplicate benchmark design

The duplicate benchmark should evaluate:

- exact duplicate detection,
- near-duplicate detection,
- copy-move and resaved document variants,
- similarity distributions across categories,
- false duplication rate versus true tampering rate.

## 6. Evaluation metrics

### Classification metrics

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC where appropriate
- False Positive Rate
- False Negative Rate

### Tamper localization metrics

- IoU
- pixel/region precision
- pixel/region recall

### Duplicate detection metrics

- similarity distribution by category
- precision at k or threshold-based precision
- recall for duplicate families
- false duplicate rate

### Performance metrics

- processing time per document
- documents per minute
- concurrency capacity
- memory usage

The project must not fabricate numbers; all performance metrics are only reportable after real measurement.

## 7. Dataset alignment

The benchmark should align each document type with the most relevant dataset:

- public tamper benchmark for manipulation localization,
- public duplicate benchmark for copy and near-duplicate detection,
- document OCR datasets for field extraction and layout benchmarking,
- synthetic benchmark generation for controlled transform families.

## 8. Future implementation guardrails

- keep benchmark and production code separate,
- snapshot configuration and dataset versions,
- retain evaluation artifacts for comparison,
- do not hide missing or failed benchmark runs,
- preserve ground-truth labels and masks with each reported result.

## 9. Phase 0 outcome

This document defines the benchmark framework, not the final thresholds. Thresholds will eventually be learned or selected empirically from validation data.

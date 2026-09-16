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

## 9. Phase 3 benchmark preparation

The Phase 3 metadata contract is `datasets/metadata/ground_truth.csv`. It includes genuine, exact duplicate, near duplicate, tampered, and mixed classes while keeping duplicate relationship fields separate from `is_tampered`.

The deterministic local fixture uses seed `42` and currently contains:

- 2 genuine records,
- 1 exact duplicate,
- 1 near duplicate,
- 1 tampered record with a mask and bounding box,
- 1 mixed tampered-family record,
- 6 records total.

These are inventory counts only. No OCR, similarity, ELA, or fraud metrics are calculated.

## 10. Leakage prevention

Related original, duplicate, near-duplicate, and tampered variants share a `source_group_id`. The validator rejects any group whose records span train, validation, and test splits. The generated family stays in the test split, while an independent genuine source is in validation. This is intentionally conservative while the fixture is small.

## 11. Reproducible tooling

```powershell
python scripts/generate_synthetic_benchmark.py --seed 42
python scripts/validate_dataset.py
python scripts/dataset_inventory.py
python -m pytest scripts/test_dataset_framework.py -q
```

The generator creates exact byte copies, a resized/recompressed near duplicate, a controlled image-region edit, and a corresponding grayscale mask. Synthetic transformations are benchmark controls, not evidence that future detection methods generalize to real fraud.

## 12. Phase 3 limitations

External sources remain unavailable or unverified, so this phase reports no downloaded public-dataset counts. The synthetic fixture is intentionally small, contains no real sensitive documents, and cannot establish model quality or production performance. Thresholds and all detection metrics remain future work.

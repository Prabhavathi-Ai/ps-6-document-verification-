# PHASE 5 COMPLETION REPORT

## Objective

Phase 5 adds a deterministic local preprocessing pipeline that converts accepted PNG/JPEG/PDF uploads into bounded RGB PNG page artifacts under derived storage while preserving the immutable original evidence. No OCR, text extraction, duplicate detection, ELA, fraud, risk, or layout analysis is implemented.

## Supported Formats

- PNG: decoded, EXIF orientation applied when present, converted to RGB, optionally downscaled, written as derived PNG.
- JPG/JPEG: decoded, EXIF orientation applied when present, converted to RGB, optionally downscaled, written as derived PNG.
- PDF: rendered locally with PyMuPDF, page order preserved, each page written as derived RGB PNG.

Configured defaults:

- `MAX_IMAGE_WIDTH=10000`
- `MAX_IMAGE_HEIGHT=10000`
- `MAX_IMAGE_PIXELS=50000000`
- `MAX_ANALYSIS_WIDTH=2400`
- `MAX_ANALYSIS_HEIGHT=2400`
- `MAX_PDF_PAGES=20`

Low-resolution images are not upscaled. Larger images are proportionally downscaled with Pillow LANCZOS resampling. Aspect ratio is preserved.

## Processing Pipeline

1. Locate the stored original through the storage abstraction.
2. Verify the original bytes match the stored document SHA-256.
3. Reuse existing valid pages for the same configuration fingerprint, if present.
4. Decode PNG/JPEG or open/render PDF pages locally.
5. Enforce image dimensions, pixel count, and PDF page limits.
6. Apply reliable EXIF orientation metadata for images only.
7. Convert derived representations to explicit RGB PNG.
8. Write pages exclusively beneath `storage/derived/{document_id}/pages/`.
9. Store page-level preprocessing metadata in `preprocessing_pages`.
10. Recheck original integrity before committing metadata.

No OCR or interpretation is performed.

## PDF Handling

The synchronous endpoint renders PDF pages with PyMuPDF and preserves source order using `page-001`, `page-002`, and so on. Empty PDFs and render failures return controlled errors. PDFs exceeding `MAX_PDF_PAGES` return `PDF_TOO_MANY_PAGES`.

## Image Handling

Image decoding uses Pillow. Invalid images return `IMAGE_DECODE_FAILED`; dimensions or pixel counts beyond configured safety limits return `IMAGE_TOO_LARGE`. Derived pages use RGB color mode and PNG output. Image metadata records source/processed dimensions, scale factor, source/output formats, orientation, color mode, and page number.

## Derived Storage

`StorageService.save_derived()` writes with exclusive creation beneath the derived root and rejects traversal. The original remains under `storage/originals/` and is never overwritten or modified. Derived outputs are separate artifacts and are not substitutes for the authoritative original in future forensic work.

## Original Preservation

Mandatory live test used a generated two-page PDF:

- hash before preprocessing: `de340160d7e2c51f4ab980663553c9086f99a349ca67ca866e5acd1dfd76d160`
- hash after preprocessing/retrieval: `de340160d7e2c51f4ab980663553c9086f99a349ca67ca866e5acd1dfd76d160`
- bytes preserved: `True`
- derived page count: `2`
- derived dimensions: `200x100` for both pages
- derived format: `PNG`

## Idempotency

The service uses a fingerprint of preprocessing limits/configuration. A repeated request with the same document and configuration reuses existing valid page records and artifacts instead of creating duplicates. If an existing artifact is missing, the stale metadata is removed and the pages are regenerated.

## API

- `POST /api/v1/documents/{document_id}/preprocess`
- `GET /api/v1/documents/{document_id}/file` remains the unchanged-original retrieval endpoint.

The preprocessing endpoint returns document ID, reuse status, and page metadata. Controlled errors include `DOCUMENT_NOT_FOUND`, `ORIGINAL_FILE_NOT_FOUND`, `UNSUPPORTED_FORMAT`, `IMAGE_DECODE_FAILED`, `PDF_RENDER_FAILED`, `IMAGE_TOO_LARGE`, `PDF_TOO_MANY_PAGES`, `ORIGINAL_INTEGRITY_ERROR`, `PREPROCESSING_FAILED`, and `DERIVED_STORAGE_ERROR`.

Live verification:

- `/docs`: HTTP 200
- `/openapi.json`: HTTP 200
- preprocessing route present in OpenAPI: `True`
- health endpoint: HTTP 200

## Frontend

No user-facing redesign or preprocessing control was added. The existing Phase 4 portal remains unchanged and its production build passes. This phase intentionally keeps preprocessing a backend API capability rather than presenting future analysis results to users.

## Tests

### Phase 5 preprocessing tests

- Command: `cd backend; set PYTHONPATH=. && python -m pytest app/tests/test_phase5_preprocessing.py -q`
- Result: PASS, `9 passed`, one existing Starlette/httpx deprecation warning.
- Coverage: PNG, JPEG, PDF, multi-page ordering, image/PDF limits, aspect ratio, original hash/bytes, derived-only paths, idempotency, traversal safety, and missing-document errors.

### Complete backend suite

- Command: `cd backend; set PYTHONPATH=. && python -m pytest app/tests -q`
- Result: PASS, `25 passed`, one existing Starlette/httpx deprecation warning.

### Phase 3 regression

- `python scripts/validate_dataset.py`: PASS, valid metadata, 6 records, 0 errors.
- `python scripts/dataset_inventory.py`: PASS, 6 records, 0 missing files.
- `python -m pytest scripts/test_dataset_framework.py -q`: PASS, `12 passed`.
- The existing user/formatter modification to `datasets/metadata/benchmark_manifest.json` was not changed.

### Frontend build

- Command: `cd frontend; npm run build`
- Result: PASS. Vite completed successfully.

### Diagnostics

- `get_errors` reported no errors for the preprocessing service, route, model, or schema.

## Performance Baseline

Measured live with a generated two-page PDF:

- upload response: HTTP 201,
- preprocessing duration: `226.27 ms`,
- source page count: `2`,
- derived page count: `2`,
- derived page dimensions: `200x100`,
- second request: reused existing pages (`reused: true`).

This is one local development measurement, not a throughput or production-performance claim. No concurrency or batch processing was added.

## Security

- Original SHA-256 is checked before and after preprocessing.
- Original bytes are never written by preprocessing.
- Image dimensions/pixels and PDF pages are bounded.
- Derived storage uses the existing path-constrained abstraction.
- Derived writes are exclusive and cleaned up on persistence failure.
- Structured errors do not expose paths, stack traces, or library internals.
- Tests use synthetic documents only.

## Git

Phase 5 commits:

- `4f91544` — Add deterministic document preprocessing — added bounded image/PDF preprocessing, page metadata, derived storage, idempotency, API, dependency, and integrity tests.
- `3bf393a` — Document Phase 5 preprocessing evidence — added Phase 5 documentation and this measured completion report.

The existing user/formatter modification to `datasets/metadata/benchmark_manifest.json` was intentionally not changed.

## Limitations

Phase 5 does not include:

- OCR or PaddleOCR,
- text or field extraction,
- logical consistency checks,
- duplicate detection or pHash,
- embeddings or Qdrant,
- ELA or pixel/noise forensic analysis,
- layout anomaly detection,
- fraud classification or risk scoring,
- heatmaps,
- batch processing or concurrency.

Preprocessing does not determine whether a document is authentic, duplicated, or fraudulent. The original file remains the authoritative forensic source.

## Next Phase

After explicit approval, Phase 6 should address the next approved document-understanding capability while consuming these page-level preprocessing contracts. OCR and extraction are not started here.

PHASE 5 COMPLETE — AWAITING HUMAN APPROVAL

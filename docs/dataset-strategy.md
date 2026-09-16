# Dataset strategy

## 1. Objective

The project should use public, appropriately licensed, and synthetic benchmark datasets to support evaluation of OCR quality, duplicate detection, tamper localization, and forensic signal measurement without introducing privacy or legal risk.

## 2. Dataset principles

- Do not use real sensitive identity documents unless there is explicit legal authorization.
- Prefer public or synthetic datasets for benchmarking.
- Store dataset metadata separately from the repository to avoid large file payloads in Git.
- Keep benchmark datasets versioned and documented.
- Separate raw datasets from derived evaluation artifacts.

## 3. Proposed dataset catalog

### AIForge-Doc

Purpose:
- document forensics and tampering analysis

Document types:
- forms, invoices, reports, scanned documents

Authentic samples:
- genuine original documents

Forged/tampered samples:
- inserted, deleted, or altered regions

Annotations:
- may include tampered regions or synthetic modifications depending on release

Tamper masks/bounding boxes:
- possible; validate availability before use

License/access requirements:
- depends on publication and access rules; confirm before use

Approximate size:
- dataset sizes vary by release; usually moderate benchmark scale

Suitability for ELA:
- good for forensic comparison and localization studies

Suitability for duplicate testing:
- moderate when copies and resaved versions are included

Suitability for OCR:
- good for document-text extraction workflows

Suitability for layout analysis:
- moderate to good when forms and layout structure are present

### Find it again!

Purpose:
- duplicate detection and retrieval benchmarking

Document types:
- scanned documents, structured documents, image duplicates

Authentic samples:
- original and repeated document images

Forged/tampered samples:
- not primary source for tampering; useful for duplicate families

Annotations:
- duplicate grouping or near-duplicate labels may exist

Tamper masks/bounding boxes:
- generally not a primary tamper localization dataset

License/access requirements:
- confirm terms and dataset access requirements

Approximate size:
- varies; can be useful for duplication benchmark development

Suitability for ELA:
- limited unless copies include compression variations

Suitability for duplicate testing:
- very strong

Suitability for OCR:
- moderate depending on the document set

Suitability for layout analysis:
- moderate

### DocTamper

Purpose:
- document tampering detection and localization

Document types:
- scanned documents and forms with manipulated content

Authentic samples:
- non-tampered originals

Forged/tampered samples:
- tampered pages and image edits

Annotations:
- tamper masks and manipulation labels may be provided

Tamper masks/bounding boxes:
- often a core strength of the dataset

License/access requirements:
- check dataset terms and provenance before use

Approximate size:
- medium subset datasets are common

Suitability for ELA:
- strong

Suitability for duplicate testing:
- limited unless fake copies are included

Suitability for OCR:
- strong in document-settings contexts

Suitability for layout analysis:
- strong when layout structure is annotated

### SROIE

Purpose:
- OCR and key-value extraction benchmark for receipts

Document types:
- receipts and scanned payment documents

Authentic samples:
- authentic receipt documents

Forged/tampered samples:
- not a primary forgery dataset

Annotations:
- text fields and bounding boxes may be available

Tamper masks/bounding boxes:
- generally not provided for tamper localization

License/access requirements:
- public competitive benchmark with clear access terms

Approximate size:
- moderate; typically several thousand samples

Suitability for ELA:
- limited for forensic anomaly analysis

Suitability for duplicate testing:
- moderate for duplicate receipts and repeated templates

Suitability for OCR:
- very strong

Suitability for layout analysis:
- strong

### CORD

Purpose:
- receipt OCR and document understanding benchmark

Document types:
- receipts and structured documents

Authentic samples:
- authentic receipts

Forged/tampered samples:
- not a primary tamper benchmark

Annotations:
- OCR labels, field labels, and layout structure

Tamper masks/bounding boxes:
- not typically included

License/access requirements:
- public benchmark dataset; verify terms

Approximate size:
- moderate

Suitability for ELA:
- limited

Suitability for duplicate testing:
- moderate

Suitability for OCR:
- very strong

Suitability for layout analysis:
- strong

## 4. Additional dataset considerations

Synthetic dataset generation may be valuable for:

- controlled duplicate families,
- known compression and resize operations,
- labeled tamper insertion and deletion scenarios,
- evaluation of suspicious-region localization at scale.

The synthetic data should be generated with documented metadata, including transformation parameters.

## 5. Dataset directory plan

The repository should include only lightweight metadata and scripts, not the large files themselves.

datasets/
├── public/
├── synthetic/
├── benchmark/
├── metadata/
└── README.md

## 6. Data handling policy

- Store only authorized public or synthetic data.
- Exclude dataset directories from Git tracking via .gitignore when appropriate.
- Provide manifest files describing origin, version, and download process.
- Record licensing and retrieval instructions.

## 7. Phase 0 status

This is a planning document only. No large datasets are downloaded or ingested in Phase 0.

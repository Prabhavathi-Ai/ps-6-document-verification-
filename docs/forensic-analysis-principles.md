# Forensic analysis principles

## 1. Core rule

No single forensic signal is sufficient to conclude fraud. The system should interpret forensic evidence as a set of independent signals that, when combined, support a risk assessment.

## 2. Required terminology

Use language such as:

- potential tampering signal
- forensic anomaly
- suspicious region
- duplicate similarity
- near-duplicate similarity
- validation inconsistency
- risk indicator

Avoid absolute phrasing such as:

- ELA proves fraud
- this document is definitely fake
- pixel noise proves manipulation

## 3. Evidence model

Each result should carry:

- the signal type,
- the calculation method,
- confidence or uncertainty,
- the region or field implicated,
- the source artifact used,
- whether the signal agrees or conflicts with other evidence.

## 4. Recommended signal categories

### Duplicate and similarity signals

- exact duplicate similarity
- near-duplicate similarity
- semantic similarity mismatch
- text embedding distance
- perceptual hash similarity

### Validation-related signals

- field inconsistency
- missing or conflicting extracted values
- format mismatch
- document template mismatch

### Forensic image signals

- ELA high-error region
- pixel noise anomaly
- spatial anomaly
- document layout anomaly
- copied-region suspicion

## 5. Interpretation standards

- A suspicious region is evidence of a possible anomaly, not definitive proof.
- Duplicate similarities must be separated from tampering evidence.
- Validation inconsistencies should be tied to the underlying extracted data.
- Risk scoring should combine multiple independent signals rather than relying on a single metric.

## 6. Explainability requirement

All final outputs should be explainable in human-readable form. Each risk indicator should refer to the evidence source and the evidence category.

## 7. Phase 0 outcome

This document establishes the language and evidence boundaries that the system must maintain in all phases.

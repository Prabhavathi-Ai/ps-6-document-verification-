from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.db.models import (
    Document,
    DuplicateAnalysis,
    DuplicateCategory,
    OCRPage,
    OCRProcessing,
    OCRStatus,
    PreprocessingPage,
)
from app.storage.service import StorageService


@dataclass(frozen=True)
class SimilarityError(Exception):
    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


def compute_dhash(image_path: Path) -> int:
    """Compute 64-bit difference hash (dHash) for an image."""
    try:
        with Image.open(image_path) as img:
            resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
            if hasattr(resized, "get_flattened_data"):
                pixels = list(resized.get_flattened_data())
            else:
                pixels = list(resized.getdata())
            decimal_val = 0
            bit_index = 0
            for row in range(8):
                for col in range(8):
                    pixel_left = pixels[row * 9 + col]
                    pixel_right = pixels[row * 9 + col + 1]
                    if pixel_left > pixel_right:
                        decimal_val |= 1 << bit_index
                    bit_index += 1
            return decimal_val
    except Exception:
        return 0


def hamming_distance(hash1: int, hash2: int) -> int:
    return bin(hash1 ^ hash2).count("1")


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace for normalized text comparison."""
    clean = re.sub(r"\s+", " ", text.lower()).strip()
    return clean


def text_similarity_ratio(text1: str, text2: str) -> float:
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if not t1 and not t2:
        return 1.0
    if not t1 or not t2:
        return 0.0
    return difflib.SequenceMatcher(None, t1, t2).ratio()


@dataclass
class DocumentComparisonSignature:
    document_id: int
    document_uuid: str
    sha256_hash: str
    file_extension: str
    mime_type: str
    page_count: int
    full_text: str
    dhash: int | None = None
    artifact_hash: str | None = None


def extract_document_signature(
    database: Session,
    document: Document,
    storage: StorageService,
) -> DocumentComparisonSignature:
    pages = database.scalars(
        select(PreprocessingPage)
        .where(PreprocessingPage.document_id == document.id)
        .order_by(PreprocessingPage.page_number)
    ).all()

    dhash_val = None
    artifact_hash = None
    if pages and storage.exists(pages[0].storage_path):
        first_page_path = storage.get(pages[0].storage_path)
        dhash_val = compute_dhash(first_page_path)
        try:
            artifact_hash = hashlib.sha256(first_page_path.read_bytes()).hexdigest()
        except Exception:
            artifact_hash = None

    ocr = database.scalar(
        select(OCRProcessing)
        .options(selectinload(OCRProcessing.pages))
        .where(
            OCRProcessing.document_id == document.id,
            OCRProcessing.status == OCRStatus.COMPLETED,
        )
        .order_by(OCRProcessing.created_at.desc())
    )
    full_text = ""
    if ocr and ocr.pages:
        full_text = "\n".join(p.text for p in ocr.pages if p.text)

    return DocumentComparisonSignature(
        document_id=document.id,
        document_uuid=document.document_id,
        sha256_hash=document.sha256_hash,
        file_extension=document.file_extension,
        mime_type=document.mime_type,
        page_count=len(pages) if pages else 1,
        full_text=full_text,
        dhash=dhash_val,
        artifact_hash=artifact_hash,
    )


def compare_signatures(
    sig_a: DocumentComparisonSignature,
    sig_b: DocumentComparisonSignature,
) -> dict[str, Any]:
    # 1. Exact original byte hash match
    if sig_a.sha256_hash == sig_b.sha256_hash:
        return {
            "exact_hash_match": True,
            "text_similarity": 1.0,
            "artifact_similarity": 1.0,
            "overall_similarity": 1.0,
            "category": DuplicateCategory.DUPLICATE,
            "conflicting_fields": [],
            "rationale": "Exact byte-for-byte duplicate (identical SHA-256 digest of original upload).",
        }

    # 2. Text Similarity
    has_text = bool(sig_a.full_text.strip() and sig_b.full_text.strip())
    t_sim = text_similarity_ratio(sig_a.full_text, sig_b.full_text) if has_text else 0.0

    # 3. Visual Artifact / dHash Similarity
    has_artifact_match = bool(
        sig_a.artifact_hash
        and sig_b.artifact_hash
        and sig_a.artifact_hash == sig_b.artifact_hash
    )
    if has_artifact_match:
        a_sim = 1.0
    elif sig_a.dhash is not None and sig_b.dhash is not None:
        dist = hamming_distance(sig_a.dhash, sig_b.dhash)
        a_sim = max(0.0, 1.0 - (dist / 64.0))
    else:
        a_sim = 0.0

    # 4. Metadata Similarity
    m_sim = 0.0
    if sig_a.file_extension == sig_b.file_extension:
        m_sim += 0.5
    if sig_a.page_count == sig_b.page_count:
        m_sim += 0.5

    # 5. Detect localized conflicting fields
    # When visual layout is highly similar (or identical page artifact) but text is present
    conflicting_fields: list[str] = []
    if (a_sim >= 0.70 or has_artifact_match) and has_text:
        # Check date differences
        date_a = set(re.findall(r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b|\b\d{2}[-/.]\d{2}[-/.]\d{4}\b", sig_a.full_text))
        date_b = set(re.findall(r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b|\b\d{2}[-/.]\d{2}[-/.]\d{4}\b", sig_b.full_text))
        if date_a and date_b and date_a != date_b:
            conflicting_fields.append("date")

        # Check amount differences
        amt_a = set(re.findall(r"\$?\b\d+\.\d{2}\b", sig_a.full_text))
        amt_b = set(re.findall(r"\$?\b\d+\.\d{2}\b", sig_b.full_text))
        if amt_a and amt_b and amt_a != amt_b:
            conflicting_fields.append("amount")

        # Check document identifier differences
        id_a = set(re.findall(r"\b(?:INV|DOC|REF|#)[-A-Za-z0-9]+\b", sig_a.full_text, re.I))
        id_b = set(re.findall(r"\b(?:INV|DOC|REF|#)[-A-Za-z0-9]+\b", sig_b.full_text, re.I))
        if id_a and id_b and id_a != id_b:
            conflicting_fields.append("identifier")

    # If derived artifact hash matches AND text is identical (or neither has text)
    if has_artifact_match and (not has_text or (t_sim >= 0.98 and not conflicting_fields)):
        return {
            "exact_hash_match": True,
            "text_similarity": 1.0,
            "artifact_similarity": 1.0,
            "overall_similarity": 1.0,
            "category": DuplicateCategory.DUPLICATE,
            "conflicting_fields": [],
            "rationale": "Exact normalized derived artifact match with identical content.",
        }

    # 6. Overall similarity calculation
    # Deterministic weighted formula:
    # If text and visual both present: 50% text + 35% visual + 15% metadata
    # If only visual present: 80% visual + 20% metadata
    # If only text present: 80% text + 20% metadata
    # If neither: 100% metadata
    if has_text and (sig_a.dhash is not None and sig_b.dhash is not None or has_artifact_match):
        overall = round(0.50 * t_sim + 0.35 * a_sim + 0.15 * m_sim, 4)
    elif sig_a.dhash is not None and sig_b.dhash is not None or has_artifact_match:
        overall = round(0.80 * a_sim + 0.20 * m_sim, 4)
    elif has_text:
        overall = round(0.80 * t_sim + 0.20 * m_sim, 4)
    else:
        overall = round(m_sim, 4)

    # 7. Category classification based on evidence thresholds:
    # - TAMPERED: High visual/structural similarity (>= 0.70) with conflicting critical fields (amount, date, identifier)
    # - DUPLICATE: Very high similarity (>= 0.98) across all dimensions without conflicts
    # - NEAR_DUPLICATE: High similarity (>= 0.85)
    # - MIXED: Intermediate similarity (0.40 <= score < 0.85)
    # - GENUINE: Distinct document (score < 0.40)
    if conflicting_fields and (a_sim >= 0.70 or overall >= 0.60):
        category = DuplicateCategory.TAMPERED
        rationale = (
            f"High structural similarity ({overall * 100:.1f}%) with conflicting critical fields "
            f"({', '.join(conflicting_fields)}), indicating potential localized alteration."
        )
    elif overall >= 0.98 and (not has_text or t_sim >= 0.98):
        category = DuplicateCategory.DUPLICATE
        rationale = f"Very high content similarity ({overall * 100:.1f}%) with identical structure."
    elif overall >= 0.85:
        category = DuplicateCategory.NEAR_DUPLICATE
        rationale = (
            f"High overall similarity ({overall * 100:.1f}%) consistent with format recompression, "
            f"scaling, or near-duplicate reproduction."
        )
    elif overall >= 0.40:
        category = DuplicateCategory.MIXED
        rationale = (
            f"Partial similarity ({overall * 100:.1f}%); inconclusive evidence to classify "
            f"as pure duplicate or tampered."
        )
    else:
        category = DuplicateCategory.GENUINE
        rationale = f"Low similarity ({overall * 100:.1f}%); distinct document."

    return {
        "exact_hash_match": False,
        "text_similarity": round(t_sim, 4),
        "artifact_similarity": round(a_sim, 4),
        "overall_similarity": overall,
        "category": category,
        "conflicting_fields": conflicting_fields,
        "rationale": rationale,
    }


def run_duplicate_check(
    database: Session,
    document_id: str,
    storage: StorageService,
    target_document_id: str | None = None,
) -> tuple[DuplicateAnalysis, bool]:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise SimilarityError("DOCUMENT_NOT_FOUND", "Document not found.", 404)

    # Check for existing analysis on unchanged state if comparing repository
    if not target_document_id:
        existing = database.scalar(
            select(DuplicateAnalysis)
            .where(DuplicateAnalysis.document_id == document.id)
            .order_by(DuplicateAnalysis.created_at.desc())
        )
        if existing:
            return existing, True

    sig_source = extract_document_signature(database, document, storage)

    # Build comparison pool: either specified target_document_id or all other documents in repository
    if target_document_id:
        target_doc = database.scalar(
            select(Document).where(Document.document_id == target_document_id)
        )
        if target_doc is None:
            raise SimilarityError(
                "TARGET_DOCUMENT_NOT_FOUND", "Target comparison document not found.", 404
            )
        pool = [target_doc]
    else:
        pool = database.scalars(
            select(Document).where(Document.id != document.id).order_by(Document.created_at.desc())
        ).all()

    if not pool:
        # Repository has no other documents to compare against
        analysis = DuplicateAnalysis(
            document_id=document.id,
            matched_document_id=None,
            matched_document_uuid=None,
            exact_hash_match=False,
            similarity_score=0.0,
            text_similarity=0.0,
            artifact_similarity=0.0,
            category=DuplicateCategory.GENUINE,
            evidence_json=json.dumps({
                "exact_hash_match": False,
                "text_similarity": 0.0,
                "artifact_similarity": 0.0,
                "overall_similarity": 0.0,
                "rationale": "No other documents in the repository for comparison; classified as genuine.",
                "conflicting_fields": [],
                "comparison_details": {},
            }),
        )
        database.add(analysis)
        database.commit()
        database.refresh(analysis)
        return analysis, False

    # Find highest similarity match in the pool
    best_match_doc: Document | None = None
    best_comparison: dict[str, Any] | None = None

    for candidate in pool:
        sig_candidate = extract_document_signature(database, candidate, storage)
        comp = compare_signatures(sig_source, sig_candidate)
        if (
            best_comparison is None
            or comp["overall_similarity"] > best_comparison["overall_similarity"]
        ):
            best_comparison = comp
            best_match_doc = candidate
            if comp["exact_hash_match"]:
                break  # Can't beat exact duplicate

    assert best_comparison is not None
    assert best_match_doc is not None

    evidence_payload = {
        "exact_hash_match": best_comparison["exact_hash_match"],
        "text_similarity": best_comparison["text_similarity"],
        "artifact_similarity": best_comparison["artifact_similarity"],
        "overall_similarity": best_comparison["overall_similarity"],
        "rationale": best_comparison["rationale"],
        "conflicting_fields": best_comparison["conflicting_fields"],
        "comparison_details": {
            "matched_document_uuid": best_match_doc.document_id,
            "matched_document_filename": best_match_doc.original_filename,
        },
    }

    record = DuplicateAnalysis(
        document_id=document.id,
        matched_document_id=best_match_doc.id,
        matched_document_uuid=best_match_doc.document_id,
        exact_hash_match=best_comparison["exact_hash_match"],
        similarity_score=best_comparison["overall_similarity"],
        text_similarity=best_comparison["text_similarity"],
        artifact_similarity=best_comparison["artifact_similarity"],
        category=best_comparison["category"],
        evidence_json=json.dumps(evidence_payload),
    )
    database.add(record)
    database.commit()
    database.refresh(record)
    return record, False

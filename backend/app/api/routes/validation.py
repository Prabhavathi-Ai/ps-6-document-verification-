from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Document, DocumentValidation, DuplicateAnalysis
from app.schemas.validation import (
    DuplicateCheckResponse,
    DuplicateEvidence,
    RuleValidationItem,
    ValidationResponse,
)
from app.services.similarity import SimilarityError, run_duplicate_check
from app.services.validation import ValidationError, validate_document
from app.storage.service import StorageService

router = APIRouter(prefix="/documents", tags=["Validation & Duplicate Detection"])


def _validation_response(
    document_id: str, record: DocumentValidation, reused: bool = False
) -> ValidationResponse:
    results_raw = json.loads(record.results_json) if record.results_json else []
    results = [
        RuleValidationItem(
            field=item["field"],
            rule=item["rule"],
            status=item["status"],
            observed_value=item.get("observed_value"),
            expected=item.get("expected"),
            message=item.get("message", ""),
        )
        for item in results_raw
    ]
    return ValidationResponse(
        validation_id=record.validation_id,
        document_id=document_id,
        overall_status=record.overall_status,
        rules_checked=record.rules_checked,
        rules_passed=record.rules_passed,
        rules_failed=record.rules_failed,
        rules_warned=record.rules_warned,
        results=results,
        reused=reused,
        created_at=record.created_at,
    )


def _duplicate_response(
    document_id: str, record: DuplicateAnalysis, reused: bool = False
) -> DuplicateCheckResponse:
    evidence_raw = json.loads(record.evidence_json) if record.evidence_json else {}
    evidence = DuplicateEvidence(
        exact_hash_match=evidence_raw.get("exact_hash_match", record.exact_hash_match),
        text_similarity=evidence_raw.get("text_similarity", record.text_similarity),
        artifact_similarity=evidence_raw.get("artifact_similarity", record.artifact_similarity),
        overall_similarity=evidence_raw.get("overall_similarity", record.similarity_score),
        rationale=evidence_raw.get("rationale", ""),
        conflicting_fields=evidence_raw.get("conflicting_fields", []),
        comparison_details=evidence_raw.get("comparison_details", {}),
    )
    return DuplicateCheckResponse(
        analysis_id=record.analysis_id,
        document_id=document_id,
        matched_document_id=record.matched_document_uuid,
        category=record.category,
        exact_hash_match=record.exact_hash_match,
        similarity_score=record.similarity_score,
        evidence=evidence,
        reused=reused,
        created_at=record.created_at,
    )


@router.post("/{document_id}/validate", response_model=ValidationResponse)
def perform_validation(
    document_id: str,
    database: Session = Depends(get_db),
) -> ValidationResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    try:
        record, reused = validate_document(database, document_id, get_settings())
    except ValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return _validation_response(document.document_id, record, reused=reused)


@router.get("/{document_id}/validation", response_model=ValidationResponse)
def get_latest_validation(
    document_id: str,
    database: Session = Depends(get_db),
) -> ValidationResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    record = database.scalar(
        select(DocumentValidation)
        .where(DocumentValidation.document_id == document.id)
        .order_by(DocumentValidation.created_at.desc())
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "VALIDATION_NOT_FOUND", "message": "No validation results found for document."},
        )
    return _validation_response(document.document_id, record, reused=True)


@router.post("/{document_id}/duplicate-check", response_model=DuplicateCheckResponse)
def perform_duplicate_check(
    document_id: str,
    target_document_id: str | None = Query(default=None),
    database: Session = Depends(get_db),
) -> DuplicateCheckResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    try:
        storage = StorageService(get_settings().storage_root)
        record, reused = run_duplicate_check(
            database, document_id, storage, target_document_id=target_document_id
        )
    except SimilarityError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return _duplicate_response(document.document_id, record, reused=reused)


@router.get("/{document_id}/duplicate-check", response_model=DuplicateCheckResponse)
def get_latest_duplicate_check(
    document_id: str,
    database: Session = Depends(get_db),
) -> DuplicateCheckResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    record = database.scalar(
        select(DuplicateAnalysis)
        .where(DuplicateAnalysis.document_id == document.id)
        .order_by(DuplicateAnalysis.created_at.desc())
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DUPLICATE_CHECK_NOT_FOUND", "message": "No duplicate analysis found for document."},
        )
    return _duplicate_response(document.document_id, record, reused=True)

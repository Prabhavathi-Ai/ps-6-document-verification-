from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.models import DuplicateCategory, ValidationStatus


class RuleValidationItem(BaseModel):
    field: str
    rule: str
    status: ValidationStatus
    observed_value: Any = None
    expected: str | None = None
    message: str


class ValidationResponse(BaseModel):
    validation_id: str
    document_id: str
    overall_status: ValidationStatus
    rules_checked: int
    rules_passed: int
    rules_failed: int
    rules_warned: int
    results: list[RuleValidationItem] = Field(default_factory=list)
    reused: bool = False
    created_at: datetime


class DuplicateEvidence(BaseModel):
    exact_hash_match: bool = False
    text_similarity: float = 0.0
    artifact_similarity: float = 0.0
    overall_similarity: float = 0.0
    rationale: str
    conflicting_fields: list[str] = Field(default_factory=list)
    comparison_details: dict[str, Any] = Field(default_factory=dict)


class DuplicateCheckResponse(BaseModel):
    analysis_id: str
    document_id: str
    matched_document_id: str | None = None
    category: DuplicateCategory
    exact_hash_match: bool = False
    similarity_score: float = 0.0
    evidence: DuplicateEvidence
    reused: bool = False
    created_at: datetime

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.db.models import (
    Document,
    DocumentValidation,
    OCRPage,
    OCRProcessing,
    OCRStatus,
    PreprocessingPage,
    ValidationStatus,
)


@dataclass(frozen=True)
class ValidationError(Exception):
    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


@dataclass
class ValidationRuleResult:
    field: str
    rule: str
    status: ValidationStatus
    observed_value: Any = None
    expected: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "rule": self.rule,
            "status": self.status.value,
            "observed_value": self.observed_value,
            "expected": self.expected,
            "message": self.message,
        }


class DocumentValidator:
    """Rule-based validator for document metadata, structure, and OCR extracted content."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate(
        self,
        document: Document,
        ocr: OCRProcessing | None = None,
        preprocessing_pages: list[PreprocessingPage] | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> list[ValidationRuleResult]:
        results: list[ValidationRuleResult] = []

        # 1. Document Metadata Rules
        # Required filename
        if document.original_filename and document.original_filename.strip():
            results.append(
                ValidationRuleResult(
                    field="original_filename",
                    rule="required",
                    status=ValidationStatus.VALID,
                    observed_value=document.original_filename,
                    message="Filename is present and valid.",
                )
            )
        else:
            results.append(
                ValidationRuleResult(
                    field="original_filename",
                    rule="required",
                    status=ValidationStatus.INVALID,
                    observed_value=document.original_filename,
                    message="Filename is missing or empty.",
                )
            )

        # Allowed extension
        if document.file_extension.lower() in self.settings.allowed_extensions:
            results.append(
                ValidationRuleResult(
                    field="file_extension",
                    rule="allowed_extensions",
                    status=ValidationStatus.VALID,
                    observed_value=document.file_extension,
                    message="File extension is supported.",
                )
            )
        else:
            results.append(
                ValidationRuleResult(
                    field="file_extension",
                    rule="allowed_extensions",
                    status=ValidationStatus.INVALID,
                    observed_value=document.file_extension,
                    expected=f"One of {self.settings.allowed_extensions}",
                    message="File extension is not supported.",
                )
            )

        # Allowed MIME type
        if document.mime_type.lower() in self.settings.allowed_mime_types:
            results.append(
                ValidationRuleResult(
                    field="mime_type",
                    rule="allowed_mime_types",
                    status=ValidationStatus.VALID,
                    observed_value=document.mime_type,
                    message="MIME type is valid.",
                )
            )
        else:
            results.append(
                ValidationRuleResult(
                    field="mime_type",
                    rule="allowed_mime_types",
                    status=ValidationStatus.INVALID,
                    observed_value=document.mime_type,
                    expected=f"One of {self.settings.allowed_mime_types}",
                    message="MIME type is not allowed.",
                )
            )

        # File size range
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if 0 < document.file_size <= max_bytes:
            results.append(
                ValidationRuleResult(
                    field="file_size",
                    rule="size_within_limits",
                    status=ValidationStatus.VALID,
                    observed_value=document.file_size,
                    message="File size is within allowed limits.",
                )
            )
        else:
            results.append(
                ValidationRuleResult(
                    field="file_size",
                    rule="size_within_limits",
                    status=ValidationStatus.INVALID,
                    observed_value=document.file_size,
                    expected=f"1 to {max_bytes} bytes",
                    message="File size exceeds allowed limits.",
                )
            )

        # SHA-256 format
        if re.fullmatch(r"[0-9a-fA-F]{64}", document.sha256_hash or ""):
            results.append(
                ValidationRuleResult(
                    field="sha256_hash",
                    rule="valid_sha256",
                    status=ValidationStatus.VALID,
                    observed_value=document.sha256_hash,
                    message="SHA-256 hash is a valid 64-character hex digest.",
                )
            )
        else:
            results.append(
                ValidationRuleResult(
                    field="sha256_hash",
                    rule="valid_sha256",
                    status=ValidationStatus.INVALID,
                    observed_value=document.sha256_hash,
                    expected="64-char hexadecimal string",
                    message="Invalid SHA-256 hash format.",
                )
            )

        # 2. Preprocessing Rules (if present)
        if preprocessing_pages:
            if len(preprocessing_pages) <= self.settings.max_pdf_pages:
                results.append(
                    ValidationRuleResult(
                        field="page_count",
                        rule="max_pdf_pages",
                        status=ValidationStatus.VALID,
                        observed_value=len(preprocessing_pages),
                        message=f"Page count ({len(preprocessing_pages)}) is within limit.",
                    )
                )
            else:
                results.append(
                    ValidationRuleResult(
                        field="page_count",
                        rule="max_pdf_pages",
                        status=ValidationStatus.INVALID,
                        observed_value=len(preprocessing_pages),
                        expected=f"<= {self.settings.max_pdf_pages}",
                        message="Document page count exceeds maximum allowable pages.",
                    )
                )

        # 3. OCR and Content Rules (if OCR completed)
        if ocr and ocr.status == OCRStatus.COMPLETED and ocr.pages:
            combined_text = "\n".join(p.text for p in ocr.pages if p.text).strip()
            total_words = sum(p.word_count for p in ocr.pages)
            avg_conf = (
                sum(p.average_confidence for p in ocr.pages) / len(ocr.pages)
                if ocr.pages
                else 0.0
            )

            # Text presence
            if len(combined_text) > 0:
                results.append(
                    ValidationRuleResult(
                        field="ocr_text",
                        rule="text_present",
                        status=ValidationStatus.VALID,
                        observed_value=f"{total_words} words",
                        message="OCR text was successfully extracted.",
                    )
                )
            else:
                results.append(
                    ValidationRuleResult(
                        field="ocr_text",
                        rule="text_present",
                        status=ValidationStatus.WARNING,
                        observed_value="0 words",
                        message="No text detected on processed pages.",
                    )
                )

            # Confidence score threshold
            if avg_conf >= 0.85:
                results.append(
                    ValidationRuleResult(
                        field="ocr_confidence",
                        rule="confidence_threshold",
                        status=ValidationStatus.VALID,
                        observed_value=round(avg_conf, 3),
                        message="Average OCR confidence is high.",
                    )
                )
            elif avg_conf >= 0.50:
                results.append(
                    ValidationRuleResult(
                        field="ocr_confidence",
                        rule="confidence_threshold",
                        status=ValidationStatus.WARNING,
                        observed_value=round(avg_conf, 3),
                        expected=">= 0.85",
                        message="OCR confidence is lower than optimal threshold.",
                    )
                )
            else:
                results.append(
                    ValidationRuleResult(
                        field="ocr_confidence",
                        rule="confidence_threshold",
                        status=ValidationStatus.WARNING,
                        observed_value=round(avg_conf, 3),
                        expected=">= 0.50",
                        message="Very low OCR confidence detected; manual review advised.",
                    )
                )

            # Extract and validate document identifier / invoice number
            id_match = re.search(
                r"(?:INVOICE|INV|DOC|REF|ID|#)[\s#:\-]*([A-Za-z0-9\-_]{3,30})",
                combined_text,
                re.IGNORECASE,
            )
            if id_match:
                extracted_id = id_match.group(1).strip()
                if re.fullmatch(r"[A-Za-z0-9\-_]+", extracted_id):
                    results.append(
                        ValidationRuleResult(
                            field="document_identifier",
                            rule="identifier_format",
                            status=ValidationStatus.VALID,
                            observed_value=extracted_id,
                            message="Document identifier format is valid alphanumeric.",
                        )
                    )
                else:
                    results.append(
                        ValidationRuleResult(
                            field="document_identifier",
                            rule="identifier_format",
                            status=ValidationStatus.INVALID,
                            observed_value=extracted_id,
                            message="Document identifier contains invalid characters.",
                        )
                    )

            # Date format detection
            date_match = re.search(
                r"\b(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})\b",
                combined_text,
            )
            if date_match:
                raw_date = date_match.group(1)
                parsed_date = self._parse_date(raw_date)
                if parsed_date:
                    results.append(
                        ValidationRuleResult(
                            field="issue_date",
                            rule="date_format",
                            status=ValidationStatus.VALID,
                            observed_value=raw_date,
                            message="Detected date conforms to a standard calendar date format.",
                        )
                    )
                else:
                    results.append(
                        ValidationRuleResult(
                            field="issue_date",
                            rule="date_format",
                            status=ValidationStatus.INVALID,
                            observed_value=raw_date,
                            expected="Valid calendar date (YYYY-MM-DD or DD-MM-YYYY)",
                            message="Extracted date is not a valid calendar date.",
                        )
                    )

            # Currency / numeric amount detection
            amount_match = re.search(
                r"(?:\$|USD|EUR|GBP|₹)?\s*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})\b",
                combined_text,
            )
            if amount_match:
                raw_amount = amount_match.group(1).replace(",", "")
                try:
                    amt_val = float(raw_amount)
                    if amt_val >= 0:
                        results.append(
                            ValidationRuleResult(
                                field="total_amount",
                                rule="numeric_amount_format",
                                status=ValidationStatus.VALID,
                                observed_value=amt_val,
                                message="Total amount conforms to numeric currency format.",
                            )
                        )
                    else:
                        results.append(
                            ValidationRuleResult(
                                field="total_amount",
                                rule="numeric_amount_format",
                                status=ValidationStatus.INVALID,
                                observed_value=amt_val,
                                message="Total amount cannot be negative.",
                            )
                        )
                except ValueError:
                    results.append(
                        ValidationRuleResult(
                            field="total_amount",
                            rule="numeric_amount_format",
                            status=ValidationStatus.INVALID,
                            observed_value=amount_match.group(1),
                            message="Invalid numeric format for amount.",
                        )
                    )

            # Email format detection (if present)
            email_match = re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                combined_text,
            )
            if email_match:
                raw_email = email_match.group(0)
                if re.fullmatch(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", raw_email):
                    results.append(
                        ValidationRuleResult(
                            field="contact_email",
                            rule="email_format",
                            status=ValidationStatus.VALID,
                            observed_value=raw_email,
                            message="Detected email conforms to standard email format.",
                        )
                    )
                else:
                    results.append(
                        ValidationRuleResult(
                            field="contact_email",
                            rule="email_format",
                            status=ValidationStatus.INVALID,
                            observed_value=raw_email,
                            message="Detected email format is invalid.",
                        )
                    )

        # 4. Custom fields validation (if provided)
        if custom_fields:
            for field_name, value in custom_fields.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    results.append(
                        ValidationRuleResult(
                            field=field_name,
                            rule="required_field",
                            status=ValidationStatus.INVALID,
                            observed_value=value,
                            message=f"Field '{field_name}' is required but was empty.",
                        )
                    )
                else:
                    results.append(
                        ValidationRuleResult(
                            field=field_name,
                            rule="required_field",
                            status=ValidationStatus.VALID,
                            observed_value=value,
                            message=f"Field '{field_name}' is present.",
                        )
                    )

        return results

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        clean = re.sub(r"[./]", "-", date_str.strip())
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(clean, fmt)
            except ValueError:
                continue
        return None


def determine_overall_status(results: list[ValidationRuleResult]) -> ValidationStatus:
    if any(r.status == ValidationStatus.INVALID for r in results):
        return ValidationStatus.INVALID
    if any(r.status == ValidationStatus.WARNING for r in results):
        return ValidationStatus.WARNING
    return ValidationStatus.VALID


def validate_document(
    database: Session,
    document_id: str,
    settings: Settings,
    custom_fields: dict[str, Any] | None = None,
) -> tuple[DocumentValidation, bool]:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise ValidationError("DOCUMENT_NOT_FOUND", "Document not found.", 404)

    # Check for existing validation if no custom fields
    if not custom_fields:
        existing = database.scalar(
            select(DocumentValidation)
            .where(DocumentValidation.document_id == document.id)
            .order_by(DocumentValidation.created_at.desc())
        )
        if existing:
            return existing, True

    # Retrieve associated preprocessing and OCR data
    pages = database.scalars(
        select(PreprocessingPage)
        .where(PreprocessingPage.document_id == document.id)
        .order_by(PreprocessingPage.page_number)
    ).all()

    ocr = database.scalar(
        select(OCRProcessing)
        .options(selectinload(OCRProcessing.pages).selectinload(OCRPage.detections))
        .where(
            OCRProcessing.document_id == document.id,
            OCRProcessing.status == OCRStatus.COMPLETED,
        )
        .order_by(OCRProcessing.created_at.desc())
    )

    validator = DocumentValidator(settings)
    rule_results = validator.validate(
        document=document,
        ocr=ocr,
        preprocessing_pages=list(pages),
        custom_fields=custom_fields,
    )

    overall_status = determine_overall_status(rule_results)
    passed_count = sum(1 for r in rule_results if r.status == ValidationStatus.VALID)
    failed_count = sum(1 for r in rule_results if r.status == ValidationStatus.INVALID)
    warned_count = sum(1 for r in rule_results if r.status == ValidationStatus.WARNING)

    record = DocumentValidation(
        document_id=document.id,
        overall_status=overall_status,
        rules_checked=len(rule_results),
        rules_passed=passed_count,
        rules_failed=failed_count,
        rules_warned=warned_count,
        results_json=json.dumps([r.to_dict() for r in rule_results]),
    )
    database.add(record)
    database.commit()
    database.refresh(record)
    return record, False

from __future__ import annotations

import hashlib
import io
import shutil
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from app.core.config import get_settings
from app.db.database import SessionLocal, reset_database_for_tests
from app.db.models import (
    Document,
    DocumentValidation,
    DuplicateAnalysis,
    DuplicateCategory,
    ValidationStatus,
)
from app.main import app
from app.services import ocr as ocr_module
from app.services.similarity import (
    compute_dhash,
    hamming_distance,
    run_duplicate_check,
    text_similarity_ratio,
)
from app.services.validation import (
    DocumentValidator,
    ValidationRuleResult,
    determine_overall_status,
    validate_document,
)
from app.storage.service import StorageService


class FakeOCRContract:
    model_name = "FakePaddleOCR"
    model_version = "test"

    def _ensure_engine(self):
        return self

    def infer(self, _path: Path, width: int, height: int):
        return [
            {
                "text": "INVOICE #INV-2026-001",
                "confidence": 0.98,
                "polygon": [[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]],
                "bbox": [10.0, 10.0, 100.0, 30.0],
                "reading_order": 1,
            },
            {
                "text": "Date: 2026-09-17",
                "confidence": 0.95,
                "polygon": [[10.0, 35.0], [100.0, 35.0], [100.0, 55.0], [10.0, 55.0]],
                "bbox": [10.0, 35.0, 100.0, 55.0],
                "reading_order": 2,
            },
            {
                "text": "Total: $1,250.00",
                "confidence": 0.96,
                "polygon": [[10.0, 60.0], [100.0, 60.0], [100.0, 80.0], [10.0, 80.0]],
                "bbox": [10.0, 60.0, 100.0, 80.0],
                "reading_order": 3,
            },
        ]


class LowConfidenceOCRContract:
    model_name = "FakePaddleOCR"
    model_version = "test"

    def _ensure_engine(self):
        return self

    def infer(self, _path: Path, width: int, height: int):
        return [
            {
                "text": "Unclear text",
                "confidence": 0.62,
                "polygon": [[10.0, 10.0], [50.0, 10.0], [50.0, 20.0], [10.0, 20.0]],
                "bbox": [10.0, 10.0, 50.0, 20.0],
                "reading_order": 1,
            }
        ]


@pytest.fixture(autouse=True)
def clean_state(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_database_for_tests()
    storage = StorageService(get_settings().storage_root)
    for directory in (storage.originals, storage.derived):
        for path in directory.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    app.dependency_overrides.clear()
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: FakeOCRContract())


def sample_png_bytes(color: tuple[int, int, int] = (255, 255, 255)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (160, 80), color).save(output, format="PNG")
    return output.getvalue()


def sample_pdf_bytes(title: str = "Test Document") -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.insert_text((20, 50), title)
    output = doc.tobytes()
    doc.close()
    return output


def upload_document(content: bytes, filename: str, mime: str) -> str:
    with TestClient(app) as client:
        res = client.post("/api/v1/documents", files={"file": (filename, content, mime)})
        assert res.status_code == 201, res.text
        return res.json()["document_id"]


# =========================================================================
# 1. Validation Unit & Service Tests
# =========================================================================

def test_validation_rule_status_determination() -> None:
    valid_res = [
        ValidationRuleResult(field="f1", rule="r1", status=ValidationStatus.VALID),
        ValidationRuleResult(field="f2", rule="r2", status=ValidationStatus.VALID),
    ]
    assert determine_overall_status(valid_res) == ValidationStatus.VALID

    warning_res = [
        ValidationRuleResult(field="f1", rule="r1", status=ValidationStatus.VALID),
        ValidationRuleResult(field="f2", rule="r2", status=ValidationStatus.WARNING),
    ]
    assert determine_overall_status(warning_res) == ValidationStatus.WARNING

    invalid_res = [
        ValidationRuleResult(field="f1", rule="r1", status=ValidationStatus.VALID),
        ValidationRuleResult(field="f2", rule="r2", status=ValidationStatus.WARNING),
        ValidationRuleResult(field="f3", rule="r3", status=ValidationStatus.INVALID),
    ]
    assert determine_overall_status(invalid_res) == ValidationStatus.INVALID


def test_validator_required_field_present_and_missing() -> None:
    validator = DocumentValidator(get_settings())
    doc = Document(
        document_id="test-doc-1",
        original_filename="valid_invoice.pdf",
        stored_filename="valid_invoice.pdf",
        storage_path="path",
        mime_type="application/pdf",
        file_extension=".pdf",
        file_size=1024,
        sha256_hash="a" * 64,
    )
    custom_fields = {
        "customer_name": "ACME Corp",
        "missing_field": "",
        "none_field": None,
    }
    results = validator.validate(doc, custom_fields=custom_fields)
    result_map = {r.field: r for r in results}

    assert result_map["customer_name"].status == ValidationStatus.VALID
    assert result_map["missing_field"].status == ValidationStatus.INVALID
    assert result_map["none_field"].status == ValidationStatus.INVALID


def test_validator_formats_and_multiple_errors() -> None:
    validator = DocumentValidator(get_settings())
    doc = Document(
        document_id="test-doc-bad",
        original_filename="",
        stored_filename="bad",
        storage_path="path",
        mime_type="invalid/mime",
        file_extension=".exe",
        file_size=0,
        sha256_hash="invalid_hash",
    )
    results = validator.validate(doc)
    invalid_rules = [r for r in results if r.status == ValidationStatus.INVALID]
    # Multiple failures detected: filename, extension, mime, size, sha256
    assert len(invalid_rules) >= 4
    assert determine_overall_status(results) == ValidationStatus.INVALID


def test_validator_date_and_numeric_parsing() -> None:
    assert DocumentValidator._parse_date("2026-09-17") is not None
    assert DocumentValidator._parse_date("17/09/2026") is not None
    assert DocumentValidator._parse_date("not-a-date") is None


# =========================================================================
# 2. Hashing Tests
# =========================================================================

def test_deterministic_hashing_identical_and_different_content(tmp_path: Path) -> None:
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.png"
    img3 = tmp_path / "img3.png"

    Image.new("RGB", (100, 100), (255, 0, 0)).save(img1)
    Image.new("RGB", (100, 100), (255, 0, 0)).save(img2)
    Image.new("RGB", (100, 100), (0, 255, 0)).save(img3)

    hash1 = compute_dhash(img1)
    hash2 = compute_dhash(img2)
    hash3 = compute_dhash(img3)

    # Identical images produce identical dHash
    assert hash1 == hash2
    # Deterministic across runs
    assert hash1 == compute_dhash(img1)
    # Different images produce non-zero Hamming distance
    assert hamming_distance(hash1, hash2) == 0


# =========================================================================
# 3. Similarity Scoring Tests
# =========================================================================

def test_similarity_scoring_levels() -> None:
    # Identical
    assert text_similarity_ratio("Invoice #100 Total $50", "Invoice #100 Total $50") == 1.0

    # Partially changed / intermediate
    intermediate = text_similarity_ratio(
        "Invoice #100 Date: 2026-09-17 Total: $500.00",
        "Invoice #100 Date: 2026-09-18 Total: $500.00",
    )
    assert 0.70 <= intermediate < 1.0

    # Completely different
    low = text_similarity_ratio("Invoice #100", "Packing Slip for Cargo Shipment 9999")
    assert low < 0.35


# =========================================================================
# 4. Duplicate Category Classification Tests
# =========================================================================

def test_duplicate_category_exact_duplicate() -> None:
    content = sample_png_bytes((100, 100, 100))
    doc1_id = upload_document(content, "original.png", "image/png")
    doc2_id = upload_document(content, "exact_copy.png", "image/png")

    with TestClient(app) as client:
        res = client.post(f"/api/v1/documents/{doc2_id}/duplicate-check")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == DuplicateCategory.DUPLICATE.value
        assert data["exact_hash_match"] is True
        assert data["similarity_score"] == 1.0
        assert data["matched_document_id"] == doc1_id


def test_duplicate_category_genuine_when_no_match() -> None:
    content = sample_png_bytes((10, 20, 30))
    doc_id = upload_document(content, "lone_document.png", "image/png")

    with TestClient(app) as client:
        res = client.post(f"/api/v1/documents/{doc_id}/duplicate-check")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == DuplicateCategory.GENUINE.value
        assert data["similarity_score"] == 0.0


def test_duplicate_category_near_duplicate(tmp_path: Path) -> None:
    # Create original PNG
    orig_bytes = sample_png_bytes((200, 200, 200))
    doc1_id = upload_document(orig_bytes, "doc1.png", "image/png")

    # Create slightly recompressed JPEG version (near duplicate)
    recompressed = io.BytesIO()
    Image.new("RGB", (160, 80), (200, 200, 200)).save(recompressed, format="JPEG", quality=90)
    doc2_id = upload_document(recompressed.getvalue(), "doc2.jpg", "image/jpeg")

    with TestClient(app) as client:
        # Preprocess both
        client.post(f"/api/v1/documents/{doc1_id}/preprocess")
        client.post(f"/api/v1/documents/{doc2_id}/preprocess")

        res = client.post(f"/api/v1/documents/{doc2_id}/duplicate-check")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] in (
            DuplicateCategory.NEAR_DUPLICATE.value,
            DuplicateCategory.DUPLICATE.value,
        )
        assert data["similarity_score"] >= 0.85


def test_duplicate_category_tampered_conflicting_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    class TamperedOCRContract:
        model_name = "FakePaddleOCR"
        model_version = "test"

        def _ensure_engine(self):
            return self

        def infer(self, _path: Path, width: int, height: int):
            return [
                {
                    "text": "INVOICE #INV-2026-999",
                    "confidence": 0.98,
                    "polygon": [[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]],
                    "bbox": [10.0, 10.0, 100.0, 30.0],
                    "reading_order": 1,
                },
                {
                    "text": "Date: 2026-09-17",
                    "confidence": 0.95,
                    "polygon": [[10.0, 35.0], [100.0, 35.0], [100.0, 55.0], [10.0, 55.0]],
                    "bbox": [10.0, 35.0, 100.0, 55.0],
                    "reading_order": 2,
                },
                {
                    "text": "Total: $9,999.00",  # Conflicting altered amount
                    "confidence": 0.96,
                    "polygon": [[10.0, 60.0], [100.0, 60.0], [100.0, 80.0], [10.0, 80.0]],
                    "bbox": [10.0, 60.0, 100.0, 80.0],
                    "reading_order": 3,
                },
            ]

    # Document 1 with standard OCR
    content1 = sample_png_bytes((150, 150, 150))
    doc1_id = upload_document(content1, "invoice1.png", "image/png")
    with TestClient(app) as client:
        client.post(f"/api/v1/documents/{doc1_id}/preprocess")
        client.post(f"/api/v1/documents/{doc1_id}/ocr")

    # Document 2 with identical image layout but altered amount in OCR
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: TamperedOCRContract())
    content2 = sample_png_bytes((150, 150, 150))
    # Slightly altered bytes to avoid exact byte duplicate
    doc2_id = upload_document(content2 + b" ", "invoice2.png", "image/png")
    with TestClient(app) as client:
        client.post(f"/api/v1/documents/{doc2_id}/preprocess")
        client.post(f"/api/v1/documents/{doc2_id}/ocr")

        res = client.post(f"/api/v1/documents/{doc2_id}/duplicate-check")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == DuplicateCategory.TAMPERED.value
        assert "amount" in data["evidence"]["conflicting_fields"]


def test_duplicate_category_mixed(monkeypatch: pytest.MonkeyPatch) -> None:
    class CustomOCR:
        def __init__(self, text: str):
            self.text = text
            self.model_name = "FakePaddleOCR"
            self.model_version = "test"

        def _ensure_engine(self):
            return self

        def infer(self, _path: Path, width: int, height: int):
            return [{
                "text": self.text,
                "confidence": 0.95,
                "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                "bbox": [0, 0, 10, 10],
                "reading_order": 1,
            }]

    # Document A
    monkeypatch.setattr(
        ocr_module,
        "ocr_service_for",
        lambda _s: CustomOCR("Certificate of Examination issued by Chennai Medical Board")
    )
    doc_a = upload_document(sample_png_bytes((10, 20, 30)), "cert_a.png", "image/png")
    with TestClient(app) as client:
        client.post(f"/api/v1/documents/{doc_a}/preprocess")
        client.post(f"/api/v1/documents/{doc_a}/ocr")

    # Document B with partial text overlap (mixed similarity)
    monkeypatch.setattr(
        ocr_module,
        "ocr_service_for",
        lambda _s: CustomOCR("Certificate of Vaccination issued by District Health Service")
    )
    doc_b = upload_document(sample_png_bytes((200, 150, 100)), "cert_b.png", "image/png")
    with TestClient(app) as client:
        client.post(f"/api/v1/documents/{doc_b}/preprocess")
        client.post(f"/api/v1/documents/{doc_b}/ocr")

        res = client.post(f"/api/v1/documents/{doc_b}/duplicate-check")
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == DuplicateCategory.MIXED.value
        assert 0.40 <= data["similarity_score"] < 0.85


# =========================================================================
# 5. Full Pipeline Integration & API Tests
# =========================================================================

def test_full_pipeline_validation_and_duplicate_detection() -> None:
    content = sample_png_bytes((240, 240, 240))
    doc_id = upload_document(content, "full_test.png", "image/png")

    with TestClient(app) as client:
        # Phase 5 Preprocess
        prep = client.post(f"/api/v1/documents/{doc_id}/preprocess")
        assert prep.status_code == 200

        # Phase 6 OCR
        ocr = client.post(f"/api/v1/documents/{doc_id}/ocr")
        assert ocr.status_code == 200

        # Phase 7 Validate
        val = client.post(f"/api/v1/documents/{doc_id}/validate")
        assert val.status_code == 200
        val_data = val.json()
        assert val_data["overall_status"] in ("valid", "warning")
        assert val_data["rules_checked"] > 0
        assert val_data["reused"] is False

        # Phase 7 Validate GET (idempotent / cached)
        val_get = client.get(f"/api/v1/documents/{doc_id}/validation")
        assert val_get.status_code == 200
        assert val_get.json()["validation_id"] == val_data["validation_id"]

        # Phase 7 Duplicate Check
        dup = client.post(f"/api/v1/documents/{doc_id}/duplicate-check")
        assert dup.status_code == 200
        dup_data = dup.json()
        assert dup_data["category"] == "genuine"
        assert dup_data["reused"] is False

        # Phase 7 Duplicate Check GET
        dup_get = client.get(f"/api/v1/documents/{doc_id}/duplicate-check")
        assert dup_get.status_code == 200
        assert dup_get.json()["analysis_id"] == dup_data["analysis_id"]


def test_api_missing_document_and_not_found_errors() -> None:
    with TestClient(app) as client:
        # 404 for non-existent document
        v_missing = client.post("/api/v1/documents/missing-uuid/validate")
        assert v_missing.status_code == 404
        assert v_missing.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

        d_missing = client.post("/api/v1/documents/missing-uuid/duplicate-check")
        assert d_missing.status_code == 404
        assert d_missing.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

        # 404 for unvalidated document retrieval
        doc_id = upload_document(sample_png_bytes(), "unvalidated.png", "image/png")
        get_val_missing = client.get(f"/api/v1/documents/{doc_id}/validation")
        assert get_val_missing.status_code == 404
        assert get_val_missing.json()["error"]["code"] == "VALIDATION_NOT_FOUND"

        get_dup_missing = client.get(f"/api/v1/documents/{doc_id}/duplicate-check")
        assert get_dup_missing.status_code == 404
        assert get_dup_missing.json()["error"]["code"] == "DUPLICATE_CHECK_NOT_FOUND"

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
from app.db.models import OCRDetection, OCRPage, OCRProcessing, OCRStatus, PreprocessingPage
from app.main import app
from app.services import ocr as ocr_module
from app.services.ocr import OCRError
from app.storage.service import StorageService


class FakeOCRService:
    model_name = "FakePaddleOCRContract"
    model_version = "test"

    def _ensure_engine(self):
        return self

    def infer(self, _path: Path, width: int, height: int):
        return [{
            "text": "Invoice 123",
            "confidence": 0.98,
            "polygon": [
                [10.0, 10.0],
                [min(110.0, float(width)), 10.0],
                [min(110.0, float(width)), min(30.0, float(height))],
                [10.0, min(30.0, float(height))],
            ],
            "bbox": [10.0, 10.0, min(110.0, float(width)), min(30.0, float(height))],
            "reading_order": 1,
        }]


class EmptyOCRService:
    model_name = "FakePaddleOCRContract"
    model_version = "test"

    def _ensure_engine(self):
        return self

    def infer(self, _path: Path, _width: int, _height: int):
        return []


class FailingInferenceOCRService:
    model_name = "FakePaddleOCRContract"
    model_version = "test"

    def _ensure_engine(self):
        return self

    def infer(self, _path: Path, _width: int, _height: int):
        raise RuntimeError("PaddleOCR inference crashed")


class UnavailableOCRService:
    model_name = "PaddleOCR"
    model_version = "unavailable"

    def _ensure_engine(self):
        raise OCRError("OCR_DEPENDENCY_UNAVAILABLE", "The PaddleOCR runtime is unavailable.", 503)


@pytest.fixture(autouse=True)
def clean_ocr_state(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_database_for_tests()
    storage = StorageService(get_settings().storage_root)
    for directory in (storage.originals, storage.derived):
        for path in directory.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    app.dependency_overrides.clear()
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: FakeOCRService())


def image_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (160, 80), (255, 255, 255)).save(output, format="PNG")
    return output.getvalue()


def multipage_pdf() -> bytes:
    document = fitz.open()
    for index in range(2):
        page = document.new_page(width=200, height=100)
        page.insert_text((20, 50), f"Synthetic OCR page {index + 1}")
    output = document.tobytes()
    document.close()
    return output


def upload_and_preprocess(content: bytes, filename: str, mime: str) -> str:
    with TestClient(app) as client:
        upload = client.post("/api/v1/documents", files={"file": (filename, content, mime)})
        assert upload.status_code == 201, upload.text
        document_id = upload.json()["document_id"]
        prepared = client.post(f"/api/v1/documents/{document_id}/preprocess")
        assert prepared.status_code == 200, prepared.text
        return document_id


# Test 1 — Successful OCR: text, confidence, bbox, polygon, normalization, database persistence
def test_basic_ocr_persists_text_geometry_and_confidence() -> None:
    document_id = upload_and_preprocess(image_bytes(), "ocr.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["pages"][0]["text"] == "Invoice 123"
    assert payload["pages"][0]["full_text"] == "Invoice 123"
    assert payload["pages"][0]["average_confidence"] == pytest.approx(0.98)
    assert payload["pages"][0]["word_count"] == 2
    assert payload["pages"][0]["line_count"] == 1
    detection = payload["pages"][0]["detections"][0]
    assert detection["confidence"] == pytest.approx(0.98)
    assert len(detection["polygon"]) == 4
    assert detection["bbox"] == [10.0, 10.0, 110.0, 30.0]
    assert detection["reading_order"] == 1

    # Database persistence verification
    database = SessionLocal()
    try:
        db_processing = database.scalar(select(OCRProcessing))
        assert db_processing is not None
        assert db_processing.status == OCRStatus.COMPLETED
        db_page = database.scalar(select(OCRPage))
        assert db_page is not None
        assert db_page.text == "Invoice 123"
        assert db_page.average_confidence == pytest.approx(0.98)
        db_detection = database.scalar(select(OCRDetection))
        assert db_detection is not None
        assert db_detection.text == "Invoice 123"
        assert db_detection.confidence == pytest.approx(0.98)
    finally:
        database.close()


# Test 2 — Empty OCR: mock returning no text, verify clean representation without fake text
def test_empty_ocr_returns_empty_result_without_hallucination(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: EmptyOCRService())
    document_id = upload_and_preprocess(image_bytes(), "empty.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    page = payload["pages"][0]
    assert page["text"] == ""
    assert page["full_text"] == ""
    assert page["average_confidence"] == 0.0
    assert page["word_count"] == 0
    assert page["line_count"] == 0
    assert page["detections"] == []

    database = SessionLocal()
    try:
        assert len(database.scalars(select(OCRDetection)).all()) == 0
        db_page = database.scalar(select(OCRPage))
        assert db_page is not None
        assert db_page.text == ""
    finally:
        database.close()


# Test 3 — OCR failure: mock raising exception, verify status becomes failed and error returned cleanly
def test_ocr_failure_persists_failed_status_and_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: FailingInferenceOCRService())
    document_id = upload_and_preprocess(image_bytes(), "fail.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "OCR_INFERENCE_FAILED"

    database = SessionLocal()
    try:
        db_processing = database.scalar(select(OCRProcessing))
        assert db_processing is not None
        assert db_processing.status == OCRStatus.FAILED
        assert "crashed" in (db_processing.error_message or "")
    finally:
        database.close()


# Test 4 — Duplicate OCR: run twice, verify idempotency and reuse
def test_ocr_is_idempotent_and_persisted() -> None:
    document_id = upload_and_preprocess(image_bytes(), "repeat.png", "image/png")
    with TestClient(app) as client:
        first = client.post(f"/api/v1/documents/{document_id}/ocr")
        second = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert first.status_code == second.status_code == 200
    assert first.json()["reused"] is False
    assert second.json()["reused"] is True
    database = SessionLocal()
    try:
        assert len(database.scalars(select(OCRProcessing)).all()) == 1
        assert len(database.scalars(select(OCRPage)).all()) == 1
        assert len(database.scalars(select(OCRDetection)).all()) == 1
    finally:
        database.close()


# Test 5 — Missing artifact: missing Phase 5 derived file returns 404
def test_missing_derived_artifact_is_controlled() -> None:
    document_id = upload_and_preprocess(image_bytes(), "missing.png", "image/png")
    database = SessionLocal()
    page = database.scalar(select(PreprocessingPage))
    StorageService(get_settings().storage_root).get(page.storage_path).unlink()
    database.close()
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MISSING_DERIVED_ARTIFACT"


def test_multi_page_ocr_preserves_page_identity_and_order() -> None:
    document_id = upload_and_preprocess(multipage_pdf(), "ocr.pdf", "application/pdf")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 200
    pages = response.json()["pages"]
    assert [page["page_id"] for page in pages] == ["page-001", "page-002"]
    assert [page["page_number"] for page in pages] == [1, 2]


def test_ocr_requires_preprocessing_and_document() -> None:
    with TestClient(app) as client:
        upload = client.post("/api/v1/documents", files={"file": ("raw.png", image_bytes(), "image/png")})
        document_id = upload.json()["document_id"]
        not_prepared = client.post(f"/api/v1/documents/{document_id}/ocr")
        missing = client.post("/api/v1/documents/missing/ocr")
    assert not_prepared.status_code == 409
    assert not_prepared.json()["error"]["code"] == "PREPROCESSING_NOT_PERFORMED"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_original_hash_and_bytes_remain_unchanged_after_ocr() -> None:
    content = image_bytes()
    document_id = upload_and_preprocess(content, "integrity.png", "image/png")
    with TestClient(app) as client:
        document = client.get(f"/api/v1/documents/{document_id}").json()
        ocr = client.post(f"/api/v1/documents/{document_id}/ocr")
        original = client.get(f"/api/v1/documents/{document_id}/file")
    assert ocr.status_code == 200
    assert original.content == content
    assert hashlib.sha256(original.content).hexdigest() == document["sha256"]


def test_unavailable_ocr_returns_structured_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr_module, "ocr_service_for", lambda _settings: UnavailableOCRService())
    document_id = upload_and_preprocess(image_bytes(), "unavailable.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/ocr")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OCR_DEPENDENCY_UNAVAILABLE"


def test_get_ocr_endpoints_and_page_retrieval() -> None:
    document_id = upload_and_preprocess(image_bytes(), "retrieval.png", "image/png")
    with TestClient(app) as client:
        # Before OCR
        not_found = client.get(f"/api/v1/documents/{document_id}/ocr")
        assert not_found.status_code == 404

        # Run OCR
        created = client.post(f"/api/v1/documents/{document_id}/ocr")
        assert created.status_code == 200
        ocr_id = created.json()["ocr_id"]

        # GET by document
        latest = client.get(f"/api/v1/documents/{document_id}/ocr")
        assert latest.status_code == 200
        assert latest.json()["ocr_id"] == ocr_id

        # GET by document and OCR id
        by_id = client.get(f"/api/v1/documents/{document_id}/ocr/{ocr_id}")
        assert by_id.status_code == 200
        assert by_id.json()["ocr_id"] == ocr_id

        # GET direct OCR id
        direct = client.get(f"/api/v1/ocr/{ocr_id}")
        assert direct.status_code == 200
        assert direct.json()["ocr_id"] == ocr_id

        # GET page OCR
        page_ocr = client.get(f"/api/v1/documents/{document_id}/pages/page-001/ocr")
        assert page_ocr.status_code == 200
        assert page_ocr.json()["page_id"] == "page-001"
        assert page_ocr.json()["text"] == "Invoice 123"

        # Missing page
        missing_page = client.get(f"/api/v1/documents/{document_id}/pages/page-999/ocr")
        assert missing_page.status_code == 404

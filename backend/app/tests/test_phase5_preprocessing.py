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
from app.db.models import Document, PreprocessingPage
from app.main import app
from app.storage.service import StorageError, StorageService


FIXTURE = Path(__file__).with_name("fixtures").joinpath("synthetic_document.pdf").read_bytes()


@pytest.fixture(autouse=True)
def clean_preprocessing_state() -> None:
    reset_database_for_tests()
    storage = StorageService(get_settings().storage_root)
    for directory in (storage.originals, storage.derived):
        for path in directory.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    app.dependency_overrides.clear()


def image_bytes(format_name: str = "PNG", size: tuple[int, int] = (80, 40)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, (30, 120, 220)).save(output, format=format_name)
    return output.getvalue()


def multipage_pdf(page_count: int = 2) -> bytes:
    document = fitz.open()
    for index in range(page_count):
        page = document.new_page(width=200, height=100)
        page.insert_text((20, 50), f"Synthetic page {index + 1}")
    output = document.tobytes()
    document.close()
    return output


def upload(content: bytes, filename: str, mime: str) -> str:
    with TestClient(app) as client:
        response = client.post("/api/v1/documents", files={"file": (filename, content, mime)})
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def test_png_preprocessing_succeeds_and_stores_derived_artifact() -> None:
    document_id = upload(image_bytes(), "sample.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    assert response.status_code == 200
    page = response.json()["pages"][0]
    assert page["page_id"] == "page-001"
    assert page["output_format"] == "PNG"
    assert page["color_mode"] == "RGB"
    assert page["source_width"] / page["source_height"] == pytest.approx(page["processed_width"] / page["processed_height"])
    assert page["storage_path" if "storage_path" in page else "page_id"]
    assert page["status"] == "COMPLETED"


def test_jpeg_preprocessing_succeeds() -> None:
    document_id = upload(image_bytes("JPEG"), "sample.jpg", "image/jpeg")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    assert response.status_code == 200
    assert response.json()["pages"][0]["source_format"] == "JPG"


def test_pdf_preprocessing_preserves_page_order() -> None:
    document_id = upload(multipage_pdf(), "multi.pdf", "application/pdf")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    assert response.status_code == 200
    pages = response.json()["pages"]
    assert [page["page_id"] for page in pages] == ["page-001", "page-002"]
    assert [page["page_number"] for page in pages] == [1, 2]


def test_pdf_page_limit_is_enforced() -> None:
    document_id = upload(multipage_pdf(2), "limited.pdf", "application/pdf")
    settings = get_settings()
    previous = settings.max_pdf_pages
    settings.max_pdf_pages = 1
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    finally:
        settings.max_pdf_pages = previous
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PDF_TOO_MANY_PAGES"


def test_image_limits_are_enforced() -> None:
    document_id = upload(image_bytes(size=(80, 40)), "large-pixel-count.png", "image/png")
    settings = get_settings()
    previous = settings.max_image_pixels
    settings.max_image_pixels = 100
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    finally:
        settings.max_image_pixels = previous
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "IMAGE_TOO_LARGE"


def test_original_hash_and_bytes_remain_unchanged() -> None:
    original_payload = multipage_pdf(1)
    document_id = upload(original_payload, "original.pdf", "application/pdf")
    storage = StorageService(get_settings().storage_root)
    database = SessionLocal()
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    original_path = storage.get(document.storage_path)
    before = original_path.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()
    database.close()

    with TestClient(app) as client:
        result = client.post(f"/api/v1/documents/{document_id}/preprocess")
        retrieved = client.get(f"/api/v1/documents/{document_id}/file")
    assert result.status_code == 200
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == before_hash
    assert original_path.read_bytes() == before
    assert retrieved.content == before


def test_repeated_preprocessing_reuses_existing_pages() -> None:
    document_id = upload(image_bytes(), "repeat.png", "image/png")
    with TestClient(app) as client:
        first = client.post(f"/api/v1/documents/{document_id}/preprocess")
        second = client.post(f"/api/v1/documents/{document_id}/preprocess")
    assert first.status_code == second.status_code == 200
    assert first.json()["reused"] is False
    assert second.json()["reused"] is True
    database = SessionLocal()
    try:
        assert len(database.scalars(select(PreprocessingPage)).all()) == 1
    finally:
        database.close()


def test_derived_artifact_is_outside_originals_and_path_is_safe() -> None:
    document_id = upload(image_bytes(), "safe.png", "image/png")
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{document_id}/preprocess")
    assert response.status_code == 200
    storage = StorageService(get_settings().storage_root)
    database = SessionLocal()
    try:
        page = database.scalar(select(PreprocessingPage))
        derived = storage.get(page.storage_path)
        assert page.storage_path.startswith("derived/")
        assert "originals" not in page.storage_path
        assert derived.is_file()
    finally:
        database.close()
    with pytest.raises(StorageError):
        storage.save_derived(io.BytesIO(b"bad"), "../../outside.png")


def test_missing_document_returns_controlled_error() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/documents/missing/preprocess")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

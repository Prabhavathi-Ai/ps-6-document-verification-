from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.db.database import SessionLocal, reset_database_for_tests
from app.db.models import Document, DocumentStatus
from app.main import app
from app.storage.service import StorageService


SYNTHETIC_BYTES = Path(__file__).with_name("fixtures").joinpath("synthetic_document.pdf").read_bytes()


@pytest.fixture(autouse=True)
def clean_database_and_storage() -> None:
    reset_database_for_tests()
    storage = StorageService(get_settings().storage_root)
    for path in storage.originals.glob("*"):
        path.unlink()


def test_storage_round_trip(tmp_path: Path) -> None:
    storage = StorageService(str(tmp_path / "storage"))
    storage_path = storage.save(io.BytesIO(b"synthetic bytes"), "document-id.pdf")

    assert storage.exists(storage_path)
    assert storage.get(storage_path).read_bytes() == b"synthetic bytes"

    storage.delete(storage_path)
    assert not storage.exists(storage_path)


def test_document_id_is_unique() -> None:
    database = SessionLocal()
    try:
        first = Document(
            document_id="same-id",
            original_filename="one.pdf",
            stored_filename="same-id.pdf",
            storage_path="originals/same-id.pdf",
            mime_type="application/pdf",
            file_extension=".pdf",
            file_size=1,
            sha256_hash="a" * 64,
            status=DocumentStatus.UPLOADED,
        )
        second = Document(
            document_id="same-id",
            original_filename="two.pdf",
            stored_filename="same-id-2.pdf",
            storage_path="originals/same-id-2.pdf",
            mime_type="application/pdf",
            file_extension=".pdf",
            file_size=1,
            sha256_hash="b" * 64,
            status=DocumentStatus.UPLOADED,
        )
        database.add_all([first, second])
        with pytest.raises(IntegrityError):
            database.commit()
    finally:
        database.rollback()
        database.close()


def test_upload_retrieval_listing_and_original_bytes() -> None:
    with TestClient(app) as client:
        upload = client.post(
            "/api/v1/documents",
            files={"file": ("synthetic_document.pdf", SYNTHETIC_BYTES, "application/pdf")},
        )
        assert upload.status_code == 201
        payload = upload.json()
        assert payload["original_filename"] == "synthetic_document.pdf"
        assert payload["status"] == "UPLOADED"
        assert payload["sha256"] == hashlib.sha256(SYNTHETIC_BYTES).hexdigest()

        document_id = payload["document_id"]
        retrieved = client.get(f"/api/v1/documents/{document_id}")
        assert retrieved.status_code == 200
        assert retrieved.json()["document_id"] == document_id

        listing = client.get("/api/v1/documents?page=1&page_size=1")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        assert len(listing.json()["documents"]) == 1

        original = client.get(f"/api/v1/documents/{document_id}/file")
        assert original.status_code == 200
        assert original.content == SYNTHETIC_BYTES


def test_upload_validation_errors() -> None:
    with TestClient(app) as client:
        unsupported = client.post(
            "/api/v1/documents",
            files={"file": ("notes.txt", b"not supported", "text/plain")},
        )
        assert unsupported.status_code == 415

        unsafe = client.post(
            "/api/v1/documents",
            files={"file": ("../unsafe.pdf", SYNTHETIC_BYTES, "application/pdf")},
        )
        assert unsafe.status_code == 400

        settings = get_settings()
        original_limit = settings.max_upload_size_mb
        settings.max_upload_size_mb = 1
        try:
            oversized = client.post(
                "/api/v1/documents",
                files={"file": ("large.pdf", b"x" * (1024 * 1024 + 1), "application/pdf")},
            )
        finally:
            settings.max_upload_size_mb = original_limit
        assert oversized.status_code == 413


def test_missing_document_errors() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/documents/missing").status_code == 404
        assert client.get("/api/v1/documents/missing/file").status_code == 404

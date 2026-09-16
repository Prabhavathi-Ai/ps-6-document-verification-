from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import documents as document_routes
from app.core.config import get_settings
from app.db.database import SessionLocal, get_db, reset_database_for_tests
from app.db.models import Document
from app.main import app
from app.services.document_validation import ValidationError, validate_upload
from app.storage.service import StorageService


FIXTURE = Path(__file__).with_name("fixtures").joinpath("synthetic_document.pdf").read_bytes()


@pytest.fixture(autouse=True)
def clean_phase4_state() -> None:
    reset_database_for_tests()
    storage = StorageService(get_settings().storage_root)
    for path in storage.originals.glob("*"):
        path.unlink()
    app.dependency_overrides.clear()


def image_bytes(format_name: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (12, 12), (40, 120, 220)).save(output, format=format_name)
    return output.getvalue()


def post_file(filename: str, content: bytes, mime: str) -> tuple[int, dict]:
    with TestClient(app) as client:
        response = client.post("/api/v1/documents", files={"file": (filename, content, mime)})
        return response.status_code, response.json()


def test_valid_image_is_accepted_and_hashes_original_bytes() -> None:
    content = image_bytes()
    with TestClient(app) as client:
        response = client.post("/api/v1/documents", files={"file": ("sample.png", content, "image/png")})
        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "UPLOADED"
        assert payload["sha256"] == hashlib.sha256(content).hexdigest()
        downloaded = client.get(f"/api/v1/documents/{payload['document_id']}/file")
        assert downloaded.content == content
        assert hashlib.sha256(downloaded.content).hexdigest() == payload["sha256"]


def test_identical_bytes_receive_the_same_sha256() -> None:
    first_code, first = post_file("first.pdf", FIXTURE, "application/pdf")
    second_code, second = post_file("second.pdf", FIXTURE, "application/pdf")
    assert first_code == second_code == 201
    assert first["sha256"] == second["sha256"] == hashlib.sha256(FIXTURE).hexdigest()


def test_empty_file_is_rejected_without_record() -> None:
    code, payload = post_file("empty.pdf", b"", "application/pdf")
    assert code == 400
    assert payload["error"]["code"] == "EMPTY_FILE"
    assert SessionLocal().scalar(select(Document)) is None


def test_signature_and_mime_mismatches_are_rejected() -> None:
    code, payload = post_file("fake.pdf", image_bytes(), "application/pdf")
    assert code == 400
    assert payload["error"]["code"] == "INVALID_FILE_CONTENT"

    code, payload = post_file("sample.png", image_bytes(), "application/pdf")
    assert code == 400
    assert payload["error"]["code"] == "MIME_TYPE_MISMATCH"


def test_malformed_image_and_pdf_are_rejected() -> None:
    code, payload = post_file("broken.png", b"\x89PNG\r\n\x1a\nnot-an-image", "image/png")
    assert code == 400
    assert payload["error"]["code"] == "INVALID_FILE_CONTENT"

    code, payload = post_file("broken.pdf", b"not-a-pdf", "application/pdf")
    assert code == 400
    assert payload["error"]["code"] == "INVALID_FILE_CONTENT"


def test_path_traversal_and_absolute_filenames_are_rejected() -> None:
    for filename in ("../../secret.pdf", r"..\..\secret.pdf", "/etc/passwd"):
        code, payload = post_file(filename, FIXTURE, "application/pdf")
        assert code == 400
        assert payload["error"]["code"] == "INVALID_FILENAME"
    with pytest.raises(ValidationError) as error:
        validate_upload(r"C:\Windows\secret.pdf", "application/pdf", FIXTURE, get_settings())
    assert error.value.code == "INVALID_FILENAME"


def test_pagination_and_public_response_hide_storage_paths() -> None:
    post_file("one.pdf", FIXTURE, "application/pdf")
    with TestClient(app) as client:
        assert client.get("/api/v1/documents?page=0").status_code == 422
        assert client.get("/api/v1/documents?page_size=101").status_code == 422
        payload = client.get("/api/v1/documents").json()["documents"][0]
        assert "storage_path" not in payload
        assert "stored_filename" not in payload


def test_storage_failure_does_not_create_success_record(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingStorage:
        def save(self, *_args: object, **_kwargs: object) -> str:
            raise document_routes.StorageError("simulated storage failure")

    monkeypatch.setattr(document_routes, "_storage", lambda: FailingStorage())
    code, payload = post_file("failure.pdf", FIXTURE, "application/pdf")
    assert code == 500
    assert payload["error"]["code"] == "STORAGE_ERROR"
    session = SessionLocal()
    try:
        assert session.scalar(select(Document)) is None
    finally:
        session.close()


def test_database_failure_cleans_up_stored_file(monkeypatch: pytest.MonkeyPatch) -> None:
    session = SessionLocal()

    class FailingSession:
        def __getattr__(self, name: str):
            return getattr(session, name)

        def commit(self) -> None:
            raise SQLAlchemyError("simulated database failure")

        def rollback(self) -> None:
            session.rollback()

        def close(self) -> None:
            session.close()

    def failing_database():
        yield FailingSession()

    app.dependency_overrides[get_db] = failing_database
    code, payload = post_file("database-failure.pdf", FIXTURE, "application/pdf")
    assert code == 500
    assert payload["error"]["code"] == "DATABASE_ERROR"
    assert list(StorageService(get_settings().storage_root).originals.glob("*")) == []

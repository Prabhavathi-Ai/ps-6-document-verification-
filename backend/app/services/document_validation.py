from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
import re

from PIL import Image, UnidentifiedImageError

from app.core.config import Settings

_FILENAME_PATTERN = re.compile(r"^[^/\\\x00]+$")
_SIGNATURES = {
    ".pdf": (b"%PDF-", "application/pdf"),
    ".png": (b"\x89PNG\r\n\x1a\n", "image/png"),
    ".jpg": (b"\xff\xd8\xff", "image/jpeg"),
    ".jpeg": (b"\xff\xd8\xff", "image/jpeg"),
}


@dataclass(frozen=True)
class ValidationError(Exception):
    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


def validate_upload(filename: str | None, content_type: str | None, payload: bytes, settings: Settings) -> str:
    if not filename or not _FILENAME_PATTERN.fullmatch(filename) or filename in {".", ".."}:
        raise ValidationError("INVALID_FILENAME", "The filename is invalid.", 400)
    extension = Path(filename).suffix.lower()
    if extension not in settings.allowed_extensions or extension not in _SIGNATURES:
        raise ValidationError("UNSUPPORTED_FILE_TYPE", "This file type is not supported.", 415)
    if not payload:
        raise ValidationError("EMPTY_FILE", "The uploaded file is empty.", 400)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(payload) > max_bytes:
        raise ValidationError("FILE_TOO_LARGE", "The uploaded file exceeds the maximum size.", 413)

    signature, expected_mime = _SIGNATURES[extension]
    if content_type and content_type not in settings.allowed_mime_types:
        raise ValidationError("UNSUPPORTED_FILE_TYPE", "This file type is not supported.", 415)
    if content_type and content_type != expected_mime:
        raise ValidationError("MIME_TYPE_MISMATCH", "The declared file type does not match the extension.", 400)
    if not payload.startswith(signature):
        raise ValidationError("INVALID_FILE_CONTENT", "The file content is invalid for its type.", 400)

    if extension != ".pdf":
        try:
            with Image.open(io.BytesIO(payload)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValidationError("INVALID_FILE_CONTENT", "The image content could not be decoded.", 400) from exc
    return extension

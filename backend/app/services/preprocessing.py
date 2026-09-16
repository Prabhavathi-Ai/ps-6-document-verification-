from __future__ import annotations

import hashlib
import io
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Document, PreprocessingPage, PreprocessingStatus
from app.storage.service import StorageError, StorageService


@dataclass(frozen=True)
class PreprocessingError(Exception):
    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return self.message


def _fingerprint(settings: Settings) -> str:
    values = {
        "max_analysis_width": settings.max_analysis_width,
        "max_analysis_height": settings.max_analysis_height,
        "max_image_width": settings.max_image_width,
        "max_image_height": settings.max_image_height,
        "max_image_pixels": settings.max_image_pixels,
        "max_pdf_pages": settings.max_pdf_pages,
    }
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _dimensions_allowed(width: int, height: int, settings: Settings) -> None:
    if width <= 0 or height <= 0 or width > settings.max_image_width or height > settings.max_image_height:
        raise PreprocessingError("IMAGE_TOO_LARGE", "The image dimensions exceed the configured limit.", 422)
    if width * height > settings.max_image_pixels:
        raise PreprocessingError("IMAGE_TOO_LARGE", "The image pixel count exceeds the configured limit.", 422)


def _normalize_image(payload: bytes, source_format: str, settings: Settings) -> tuple[list[dict], list[bytes]]:
    try:
        with Image.open(io.BytesIO(payload)) as opened:
            opened.verify()
        with Image.open(io.BytesIO(payload)) as opened:
            orientation_tag = opened.getexif().get(274, 1)
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PreprocessingError("IMAGE_DECODE_FAILED", "The image could not be decoded.", 422) from exc

    source_width, source_height = image.size
    _dimensions_allowed(source_width, source_height, settings)
    processed = image.copy()
    scale = min(1.0, settings.max_analysis_width / source_width, settings.max_analysis_height / source_height)
    if scale < 1.0:
        processed = processed.resize(
            (max(1, round(source_width * scale)), max(1, round(source_height * scale))),
            Image.Resampling.LANCZOS,
        )
    output = io.BytesIO()
    processed.save(output, format="PNG", optimize=False)
    metadata = {
        "page_number": 1,
        "source_width": source_width,
        "source_height": source_height,
        "processed_width": processed.width,
        "processed_height": processed.height,
        "source_format": source_format,
        "output_format": "PNG",
        "scale_factor": processed.width / source_width,
        "orientation": "EXIF_APPLIED" if orientation_tag != 1 else "NONE",
        "color_mode": "RGB",
    }
    return [metadata], [output.getvalue()]


def _normalize_pdf(payload: bytes, settings: Settings) -> tuple[list[dict], list[bytes]]:
    try:
        import fitz

        pdf = fitz.open(stream=payload, filetype="pdf")
    except Exception as exc:
        raise PreprocessingError("PDF_RENDER_FAILED", "The PDF could not be opened.", 422) from exc

    try:
        if pdf.page_count < 1:
            raise PreprocessingError("PDF_RENDER_FAILED", "The PDF contains no pages.", 422)
        if pdf.page_count > settings.max_pdf_pages:
            raise PreprocessingError("PDF_TOO_MANY_PAGES", "The PDF exceeds the configured page limit.", 422)
        pages: list[dict] = []
        outputs: list[bytes] = []
        for index in range(pdf.page_count):
            page = pdf.load_page(index)
            rect = page.rect
            source_width = max(1, round(rect.width))
            source_height = max(1, round(rect.height))
            _dimensions_allowed(source_width, source_height, settings)
            scale = min(1.0, settings.max_analysis_width / source_width, settings.max_analysis_height / source_height)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=False)
            pages.append({
                "page_number": index + 1,
                "source_width": source_width,
                "source_height": source_height,
                "processed_width": image.width,
                "processed_height": image.height,
                "source_format": "PDF",
                "output_format": "PNG",
                "scale_factor": image.width / source_width,
                "orientation": "NONE",
                "color_mode": "RGB",
            })
            outputs.append(output.getvalue())
        return pages, outputs
    except PreprocessingError:
        raise
    except Exception as exc:
        raise PreprocessingError("PDF_RENDER_FAILED", "The PDF page could not be rendered.", 422) from exc
    finally:
        pdf.close()


def preprocess_document(database: Session, document: Document, storage: StorageService, settings: Settings) -> tuple[list[PreprocessingPage], bool]:
    source_path = storage.get(document.storage_path)
    original_bytes = source_path.read_bytes()
    if _hash_bytes(original_bytes) != document.sha256_hash:
        raise PreprocessingError("ORIGINAL_INTEGRITY_ERROR", "The stored original failed its integrity check.", 409)

    fingerprint = _fingerprint(settings)
    existing = database.scalars(
        select(PreprocessingPage)
        .where(PreprocessingPage.document_id == document.id, PreprocessingPage.config_fingerprint == fingerprint)
        .order_by(PreprocessingPage.page_number)
    ).all()
    if existing and all(storage.exists(page.storage_path) for page in existing):
        return existing, True
    if existing:
        for page in existing:
            database.delete(page)
        database.commit()

    source_format = document.file_extension.upper().removeprefix(".")
    if source_format in {"PNG", "JPG", "JPEG"}:
        metadata, outputs = _normalize_image(original_bytes, source_format, settings)
    elif source_format == "PDF":
        metadata, outputs = _normalize_pdf(original_bytes, settings)
    else:
        raise PreprocessingError("UNSUPPORTED_FORMAT", "This document format cannot be preprocessed.", 415)

    stored_paths: list[str] = []
    records: list[PreprocessingPage] = []
    try:
        for page_metadata, output in zip(metadata, outputs):
            page_id = f"page-{page_metadata['page_number']:03d}"
            storage_path = storage.save_derived(
                io.BytesIO(output), f"{document.document_id}/pages/{page_id}.png"
            )
            stored_paths.append(storage_path)
            records.append(
                PreprocessingPage(
                    processing_id=str(uuid.uuid4()),
                    document_id=document.id,
                    page_id=page_id,
                    config_fingerprint=fingerprint,
                    storage_path=storage_path,
                    status=PreprocessingStatus.COMPLETED,
                    **page_metadata,
                )
            )
        if _hash_bytes(source_path.read_bytes()) != document.sha256_hash:
            raise PreprocessingError("ORIGINAL_INTEGRITY_ERROR", "The original changed during preprocessing.", 500)
        database.add_all(records)
        database.commit()
        for record in records:
            database.refresh(record)
    except (StorageError, SQLAlchemyError) as exc:
        database.rollback()
        for path in stored_paths:
            try:
                storage.delete(path)
            except (FileNotFoundError, StorageError):
                pass
        code = "DERIVED_STORAGE_ERROR" if isinstance(exc, StorageError) else "PREPROCESSING_FAILED"
        raise PreprocessingError(code, "The preprocessing result could not be stored.", 500) from exc

    if _hash_bytes(source_path.read_bytes()) != document.sha256_hash:
        raise PreprocessingError("ORIGINAL_INTEGRITY_ERROR", "The original changed during preprocessing.", 500)
    return records, False

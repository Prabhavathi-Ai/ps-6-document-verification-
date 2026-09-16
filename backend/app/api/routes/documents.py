from __future__ import annotations

import hashlib
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Document, DocumentStatus
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.storage.service import StorageError, StorageService
from app.services.document_validation import ValidationError, validate_upload

router = APIRouter(prefix="/documents", tags=["Documents"])
def _storage() -> StorageService:
    return StorageService(get_settings().storage_root)


def _response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        document_id=document.document_id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_extension=document.file_extension,
        file_size=document.file_size,
        sha256=document.sha256_hash,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), database: Session = Depends(get_db)) -> DocumentResponse:
    settings = get_settings()
    payload = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    try:
        extension = validate_upload(file.filename, file.content_type, payload, settings)
    except ValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc
    filename = file.filename

    document_id = str(uuid.uuid4())
    stored_filename = f"{document_id}{extension}"
    storage = _storage()
    sha256_hash = hashlib.sha256(payload).hexdigest()
    storage_path = ""
    try:
        storage_path = storage.save(io.BytesIO(payload), stored_filename)
        document = Document(
            document_id=document_id,
            original_filename=filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            mime_type=file.content_type or "application/octet-stream",
            file_extension=extension,
            file_size=len(payload),
            sha256_hash=sha256_hash,
            status=DocumentStatus.UPLOADED,
        )
        database.add(document)
        database.commit()
        database.refresh(document)
        return _response(document)
    except (StorageError, SQLAlchemyError) as exc:
        database.rollback()
        if storage_path:
            try:
                storage.delete(storage_path)
            except (FileNotFoundError, StorageError):
                pass
        code = "STORAGE_ERROR" if isinstance(exc, StorageError) else "DATABASE_ERROR"
        raise HTTPException(status_code=500, detail={"code": code, "message": "The document could not be stored."}) from exc


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=get_settings().max_page_size),
    database: Session = Depends(get_db),
) -> DocumentListResponse:
    total = database.scalar(select(func.count()).select_from(Document)) or 0
    documents = database.scalars(
        select(Document).order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        documents=[_response(document) for document in documents],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, database: Session = Depends(get_db)) -> DocumentResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _response(document)


@router.get("/{document_id}/file")
def get_document_file(document_id: str, database: Session = Depends(get_db)) -> FileResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        file_path = _storage().get(document.storage_path)
    except (FileNotFoundError, StorageError) as exc:
        raise HTTPException(status_code=404, detail="Stored document file not found") from exc
    return FileResponse(
        path=file_path,
        media_type=document.mime_type,
        filename=document.original_filename,
    )

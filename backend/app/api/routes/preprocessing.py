from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Document, PreprocessingPage
from app.schemas.preprocessing import PreprocessingPageResponse, PreprocessingResponse
from app.services.preprocessing import PreprocessingError, preprocess_document
from app.storage.service import StorageError, StorageService

router = APIRouter(prefix="/documents", tags=["Preprocessing"])


@router.post("/{document_id}/preprocess", response_model=PreprocessingResponse)
def preprocess(document_id: str, database: Session = Depends(get_db)) -> PreprocessingResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    try:
        pages, reused = preprocess_document(database, document, StorageService(get_settings().storage_root), get_settings())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "ORIGINAL_FILE_NOT_FOUND", "message": "The original file is unavailable."}) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail={"code": "DERIVED_STORAGE_ERROR", "message": "The derived artifact could not be stored."}) from exc
    except PreprocessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc

    return PreprocessingResponse(
        document_id=document.document_id,
        reused=reused,
        pages=[
            PreprocessingPageResponse(
                processing_id=page.processing_id,
                document_id=document.document_id,
                page_id=page.page_id,
                page_number=page.page_number,
                source_width=page.source_width,
                source_height=page.source_height,
                processed_width=page.processed_width,
                processed_height=page.processed_height,
                source_format=page.source_format,
                output_format=page.output_format,
                scale_factor=page.scale_factor,
                orientation=page.orientation,
                color_mode=page.color_mode,
                status=page.status,
                created_at=page.created_at,
            )
            for page in pages
        ],
    )


@router.get("/{document_id}/pages/{page_number}/image")
def get_page_image(
    document_id: str,
    page_number: int,
    database: Session = Depends(get_db),
) -> FileResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    page = database.scalar(
        select(PreprocessingPage)
        .where(
            PreprocessingPage.document_id == document.id,
            PreprocessingPage.page_number == page_number,
        )
    )
    if page is None:
        raise HTTPException(status_code=404, detail={"code": "PAGE_NOT_FOUND", "message": "Page not found."})
    storage = StorageService(get_settings().storage_root)
    if not storage.exists(page.storage_path):
        raise HTTPException(status_code=404, detail={"code": "PAGE_IMAGE_NOT_FOUND", "message": "Page image file not found."})
    return FileResponse(
        path=storage.get(page.storage_path),
        media_type="image/png",
    )


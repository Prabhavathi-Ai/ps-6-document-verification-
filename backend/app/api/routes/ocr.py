from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Document, OCRPage, OCRProcessing
from app.schemas.ocr import OCRDetectionResponse, OCRPageResponse, OCRResponse
from app.services.ocr import OCRError, run_ocr
from app.storage.service import StorageService

router = APIRouter(tags=["OCR"])


def _page_response(page: OCRPage) -> OCRPageResponse:
    detections = [
        OCRDetectionResponse(
            text=detection.text,
            confidence=detection.confidence,
            bbox=[detection.x1, detection.y1, detection.x2, detection.y2],
            polygon=json.loads(detection.polygon),
            reading_order=detection.reading_order,
        )
        for detection in page.detections
    ]
    return OCRPageResponse(
        ocr_page_id=page.ocr_page_id,
        page_id=page.page_id,
        page_number=page.page_number,
        image_width=page.image_width,
        image_height=page.image_height,
        text=page.text,
        full_text=page.text,
        average_confidence=page.average_confidence,
        word_count=page.word_count,
        line_count=page.line_count,
        status=page.status,
        detections=detections,
        regions=detections,
        error_message=page.error_message,
        created_at=page.created_at,
    )


def _ocr_response(document_id: str, processing: OCRProcessing, reused: bool = False) -> OCRResponse:
    return OCRResponse(
        document_id=document_id,
        ocr_id=processing.ocr_id,
        status=processing.status,
        language=processing.language,
        model_name=processing.model_name,
        model_version=processing.model_version,
        reused=reused,
        error_message=processing.error_message,
        pages=[_page_response(page) for page in processing.pages],
        created_at=processing.created_at,
    )


@router.post("/documents/{document_id}/ocr", response_model=OCRResponse)
def perform_ocr(document_id: str, database: Session = Depends(get_db)) -> OCRResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    try:
        processing, reused = run_ocr(
            database,
            document_id,
            StorageService(get_settings().storage_root),
            get_settings(),
        )
    except OCRError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return _ocr_response(document.document_id, processing, reused=reused)


@router.get("/documents/{document_id}/ocr", response_model=OCRResponse)
def get_latest_document_ocr(document_id: str, database: Session = Depends(get_db)) -> OCRResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    processing = database.scalar(
        select(OCRProcessing)
        .options(selectinload(OCRProcessing.pages).selectinload(OCRPage.detections))
        .where(OCRProcessing.document_id == document.id)
        .order_by(OCRProcessing.created_at.desc())
    )
    if processing is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "OCR_NOT_FOUND", "message": "No OCR results found for document."},
        )
    return _ocr_response(document.document_id, processing, reused=True)


@router.get("/documents/{document_id}/ocr/{ocr_id}", response_model=OCRResponse)
def get_document_ocr_by_id(
    document_id: str, ocr_id: str, database: Session = Depends(get_db)
) -> OCRResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    processing = database.scalar(
        select(OCRProcessing)
        .options(selectinload(OCRProcessing.pages).selectinload(OCRPage.detections))
        .where(OCRProcessing.ocr_id == ocr_id, OCRProcessing.document_id == document.id)
    )
    if processing is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "OCR_NOT_FOUND", "message": "OCR result not found."},
        )
    return _ocr_response(document.document_id, processing, reused=True)


@router.get("/documents/{document_id}/pages/{page_id}/ocr", response_model=OCRPageResponse)
def get_page_ocr(
    document_id: str, page_id: str, database: Session = Depends(get_db)
) -> OCRPageResponse:
    document = database.scalar(select(Document).where(Document.document_id == document_id))
    if document is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."},
        )
    page = database.scalar(
        select(OCRPage)
        .options(selectinload(OCRPage.detections))
        .where(OCRPage.document_id == document.id, OCRPage.page_id == page_id)
        .order_by(OCRPage.created_at.desc())
    )
    if page is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "OCR_PAGE_NOT_FOUND", "message": "OCR result not found for page."},
        )
    return _page_response(page)


@router.get("/ocr/{ocr_id}", response_model=OCRResponse)
def get_ocr_by_id(ocr_id: str, database: Session = Depends(get_db)) -> OCRResponse:
    processing = database.scalar(
        select(OCRProcessing)
        .options(
            selectinload(OCRProcessing.pages).selectinload(OCRPage.detections),
            selectinload(OCRProcessing.document),
        )
        .where(OCRProcessing.ocr_id == ocr_id)
    )
    if processing is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "OCR_NOT_FOUND", "message": "OCR result not found."},
        )
    doc_id = processing.document.document_id if processing.document else ""
    return _ocr_response(doc_id, processing, reused=True)

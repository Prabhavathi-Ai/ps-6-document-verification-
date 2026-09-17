from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import OCRStatus


class OCRDetectionResponse(BaseModel):
    text: str
    confidence: float
    bbox: list[float]
    polygon: list[list[float]]
    reading_order: int


class OCRPageResponse(BaseModel):
    ocr_page_id: str
    page_id: str
    page_number: int
    image_width: int
    image_height: int
    text: str
    full_text: str | None = None
    average_confidence: float = 0.0
    word_count: int
    line_count: int
    status: OCRStatus
    detections: list[OCRDetectionResponse]
    regions: list[OCRDetectionResponse] | None = None
    error_message: str | None = None
    created_at: datetime


class OCRResponse(BaseModel):
    document_id: str
    ocr_id: str
    status: OCRStatus
    language: str
    model_name: str
    model_version: str
    reused: bool = False
    error_message: str | None = None
    pages: list[OCRPageResponse] = Field(default_factory=list)
    created_at: datetime | None = None

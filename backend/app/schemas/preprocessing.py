from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.models import PreprocessingStatus


class PreprocessingPageResponse(BaseModel):
    processing_id: str
    document_id: str
    page_id: str
    page_number: int
    source_width: int
    source_height: int
    processed_width: int
    processed_height: int
    source_format: str
    output_format: str
    scale_factor: float
    orientation: str
    color_mode: str
    status: PreprocessingStatus
    created_at: datetime


class PreprocessingResponse(BaseModel):
    document_id: str
    pages: list[PreprocessingPageResponse]
    reused: bool

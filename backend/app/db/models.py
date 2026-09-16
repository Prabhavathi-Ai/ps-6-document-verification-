from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class ProcessingJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingJobType(str, enum.Enum):
    PREPROCESSING = "PREPROCESSING"
    OCR = "OCR"
    EXTRACTION = "EXTRACTION"
    VALIDATION = "VALIDATION"
    DUPLICATE_CHECK = "DUPLICATE_CHECK"
    FORENSIC_ANALYSIS = "FORENSIC_ANALYSIS"
    RISK_ANALYSIS = "RISK_ANALYSIS"


class PreprocessingStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    processing_jobs: Mapped[list[ProcessingJob]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ProcessingJob.created_at",
    )


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    job_type: Mapped[ProcessingJobType] = mapped_column(Enum(ProcessingJobType), nullable=False)
    status: Mapped[ProcessingJobStatus] = mapped_column(Enum(ProcessingJobStatus), default=ProcessingJobStatus.QUEUED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship(back_populates="processing_jobs")


class PreprocessingPage(Base):
    __tablename__ = "preprocessing_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    processing_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(128), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_width: Mapped[int] = mapped_column(Integer, nullable=False)
    source_height: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_width: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_height: Mapped[int] = mapped_column(Integer, nullable=False)
    source_format: Mapped[str] = mapped_column(String(16), nullable=False)
    output_format: Mapped[str] = mapped_column(String(16), nullable=False)
    scale_factor: Mapped[float] = mapped_column(nullable=False)
    orientation: Mapped[str] = mapped_column(String(64), nullable=False)
    color_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    config_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[PreprocessingStatus] = mapped_column(Enum(PreprocessingStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship()

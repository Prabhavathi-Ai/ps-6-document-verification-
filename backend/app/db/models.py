from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
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


class OCRStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ValidationStatus(str, enum.Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


class DuplicateCategory(str, enum.Enum):
    GENUINE = "genuine"
    DUPLICATE = "duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    TAMPERED = "tampered"
    MIXED = "mixed"


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


class OCRProcessing(Base):
    __tablename__ = "ocr_processings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocr_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    preprocessing_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[OCRStatus] = mapped_column(Enum(OCRStatus), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship()
    pages: Mapped[list[OCRPage]] = relationship(back_populates="ocr", cascade="all, delete-orphan", order_by="OCRPage.page_number")


class OCRPage(Base):
    __tablename__ = "ocr_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocr_page_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    ocr_id: Mapped[int] = mapped_column(ForeignKey("ocr_processings.id"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    image_width: Mapped[int] = mapped_column(Integer, nullable=False)
    image_height: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    average_confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OCRStatus] = mapped_column(Enum(OCRStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ocr: Mapped[OCRProcessing] = relationship(back_populates="pages")
    detections: Mapped[list[OCRDetection]] = relationship(back_populates="page", cascade="all, delete-orphan", order_by="OCRDetection.reading_order")


class OCRDetection(Base):
    __tablename__ = "ocr_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocr_page_id: Mapped[int] = mapped_column(ForeignKey("ocr_pages.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    x1: Mapped[float] = mapped_column(nullable=False)
    y1: Mapped[float] = mapped_column(nullable=False)
    x2: Mapped[float] = mapped_column(nullable=False)
    y2: Mapped[float] = mapped_column(nullable=False)
    polygon: Mapped[str] = mapped_column(Text, nullable=False)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    page: Mapped[OCRPage] = relationship(back_populates="detections")


class DocumentValidation(Base):
    __tablename__ = "document_validations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    validation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    overall_status: Mapped[ValidationStatus] = mapped_column(Enum(ValidationStatus), nullable=False)
    rules_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rules_warned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship()


class DuplicateAnalysis(Base):
    __tablename__ = "duplicate_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    matched_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    matched_document_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    exact_hash_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    text_similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    artifact_similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    category: Mapped[DuplicateCategory] = mapped_column(Enum(DuplicateCategory), nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship(foreign_keys=[document_id])
    matched_document: Mapped[Document | None] = relationship(foreign_keys=[matched_document_id])

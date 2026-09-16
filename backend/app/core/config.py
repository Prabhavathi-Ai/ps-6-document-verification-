from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="VeriDoc AI")
    environment: str = Field(default="development")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="sqlite:///./data/veridoc.db")
    storage_root: str = Field(default="./storage")
    max_upload_size_mb: int = Field(default=20, ge=1, le=500)
    max_page_size: int = Field(default=100, ge=1, le=1000)
    max_image_width: int = Field(default=10000, ge=1, le=50000)
    max_image_height: int = Field(default=10000, ge=1, le=50000)
    max_image_pixels: int = Field(default=50_000_000, ge=1_000_000, le=500_000_000)
    max_analysis_width: int = Field(default=2400, ge=1, le=10000)
    max_analysis_height: int = Field(default=2400, ge=1, le=10000)
    max_pdf_pages: int = Field(default=20, ge=1, le=1000)
    allowed_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".png", ".jpg", ".jpeg"])
    allowed_mime_types: list[str] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg"]
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

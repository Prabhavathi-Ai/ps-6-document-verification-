from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def get_health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "veridoc-api",
        "version": "0.1.0",
        "environment": settings.environment,
    }

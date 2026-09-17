from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.exceptions import HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.preprocessing import router as preprocessing_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.validation import router as validation_router
from app.core.config import get_settings
from app.db.database import initialize_database
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger("veridoc.api")

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="VeriDoc AI application foundation",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(preprocessing_router, prefix=settings.api_prefix)
app.include_router(ocr_router, prefix=settings.api_prefix)
app.include_router(validation_router, prefix=settings.api_prefix)


@app.get(settings.api_prefix)
def api_root() -> dict:
    return {
        "application": settings.app_name,
        "api_version": "v1",
        "environment": settings.environment,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning("HTTP error for %s: %s", request.url.path, exc.detail)
    if isinstance(exc.detail, dict) and {"code", "message"}.issubset(exc.detail):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception for %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

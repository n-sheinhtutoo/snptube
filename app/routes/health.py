from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models import HealthResponse
from app.services.ytdlp import check_ffmpeg

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns API health status, version, and FFmpeg availability.",
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        ffmpeg_available=check_ffmpeg(),
    )

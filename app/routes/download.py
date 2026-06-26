from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from yt_dlp.utils import DownloadError

from app.models import DownloadAudioRequest, DownloadVideoRequest, ErrorResponse
from app.services.ytdlp import YTDLPService
from app.utils.cleanup import schedule_file_deletion
from app.utils.validators import is_valid_youtube_url, sanitize_filename

logger = logging.getLogger(__name__)
router = APIRouter()

MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".opus": "audio/opus",
    ".ogg": "audio/ogg",
    ".webm": "video/webm",
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".flv": "video/x-flv",
}


def _media_type(filepath: Path) -> str:
    return MIME_MAP.get(filepath.suffix.lower(), "application/octet-stream")


def _error_detail(exc: Exception) -> str:
    msg = str(exc)
    if "is not a valid URL" in msg or "Unsupported URL" in msg:
        return "The provided URL is not supported"
    if "Video unavailable" in msg or "Private video" in msg:
        return "This video is unavailable or private"
    if "Sign in" in msg or "confirm your age" in msg:
        return "This video requires authentication and cannot be downloaded"
    if "The downloaded file is empty" in msg:
        return "Download failed (empty file). Try a different quality or try again later."
    if "Requested format is not available" in msg:
        return "The requested format is not available for this video"
    return f"Download failed: {msg}"


@router.post(
    "/download/audio",
    responses={
        200: {"content": {"audio/mpeg": {}}, "description": "Audio file"},
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    summary="Download audio",
    description="Download the audio track of a public YouTube video. Optionally converts to MP3.",
)
async def download_audio(req: DownloadAudioRequest) -> FileResponse:
    url = str(req.url)
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL")

    try:
        service = YTDLPService()
        filepath = await service.download_audio(
            url, format_id=req.format_id, convert_mp3=req.convert_mp3
        )
    except FileNotFoundError as e:
        logger.exception("Downloaded file not found")
        raise HTTPException(status_code=502, detail=str(e)) from e
    except DownloadError as e:
        logger.error("yt-dlp download error: %s", e)
        raise HTTPException(status_code=502, detail=_error_detail(e)) from e
    except Exception as e:
        logger.exception("Audio download failed")
        raise HTTPException(status_code=502, detail=_error_detail(e)) from e

    download_name = sanitize_filename(filepath.stem) + filepath.suffix
    await schedule_file_deletion(filepath, delay_seconds=60.0)

    return FileResponse(
        path=str(filepath),
        media_type=_media_type(filepath),
        filename=download_name,
    )


@router.post(
    "/download/video",
    responses={
        200: {"content": {"video/mp4": {}}, "description": "Video file"},
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    summary="Download video",
    description="Download a public YouTube video. Supports quality selection.",
)
async def download_video(req: DownloadVideoRequest) -> FileResponse:
    url = str(req.url)
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL")

    try:
        service = YTDLPService()
        filepath = await service.download_video(
            url, format_id=req.format_id, resolution=req.resolution
        )
    except FileNotFoundError as e:
        logger.exception("Downloaded file not found")
        raise HTTPException(status_code=502, detail=str(e)) from e
    except DownloadError as e:
        logger.error("yt-dlp download error: %s", e)
        raise HTTPException(status_code=502, detail=_error_detail(e)) from e
    except Exception as e:
        logger.exception("Video download failed")
        raise HTTPException(status_code=502, detail=_error_detail(e)) from e

    download_name = sanitize_filename(filepath.stem) + filepath.suffix
    await schedule_file_deletion(filepath, delay_seconds=120.0)

    return FileResponse(
        path=str(filepath),
        media_type=_media_type(filepath),
        filename=download_name,
    )

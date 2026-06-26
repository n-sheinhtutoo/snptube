from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models import (
    ErrorResponse,
    FormatInfo,
    FormatsResponse,
    URLRequest,
    VideoInfoResponse,
)
from app.services.ytdlp import YTDLPService
from app.utils.validators import is_valid_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/info",
    response_model=VideoInfoResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="Get video info",
    description="Extract metadata for a public YouTube video.",
)
async def get_video_info(req: URLRequest) -> VideoInfoResponse:
    url = str(req.url)
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL")

    try:
        service = YTDLPService()
        info = await service.extract_info(url)
    except Exception as e:
        logger.exception("Failed to extract video info")
        raise HTTPException(status_code=502, detail=f"Extraction failed: {e}") from e

    return VideoInfoResponse(
        id=info.get("id", ""),
        title=info.get("title", "Unknown"),
        duration=info.get("duration"),
        duration_string=info.get("duration_string"),
        thumbnail=info.get("thumbnail"),
        channel=info.get("channel"),
        uploader=info.get("uploader"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        upload_date=info.get("upload_date"),
        description=(info.get("description") or "")[:500] or None,
        webpage_url=info.get("webpage_url"),
    )


@router.post(
    "/formats",
    response_model=FormatsResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    summary="List available formats",
    description="List all available download formats for a public YouTube video.",
)
async def get_formats(req: URLRequest) -> FormatsResponse:
    url = str(req.url)
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL")

    try:
        service = YTDLPService()
        info = await service.extract_formats(url)
    except Exception as e:
        logger.exception("Failed to extract formats")
        raise HTTPException(status_code=502, detail=f"Extraction failed: {e}") from e

    raw_formats = info.get("formats", [])
    formats = [
        FormatInfo(
            format_id=f.get("format_id", ""),
            ext=f.get("ext", ""),
            resolution=f.get("resolution"),
            fps=f.get("fps"),
            vcodec=f.get("vcodec"),
            acodec=f.get("acodec"),
            filesize=f.get("filesize"),
            filesize_approx=f.get("filesize_approx"),
            tbr=f.get("tbr"),
            note=f.get("format_note"),
        )
        for f in raw_formats
        if f.get("format_id")
    ]

    return FormatsResponse(
        id=info.get("id", ""),
        title=info.get("title", "Unknown"),
        formats=formats,
    )

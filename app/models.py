from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class URLRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube video URL")


class DownloadAudioRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube video URL")
    format_id: str | None = Field(
        None, description="Specific format ID to download"
    )
    convert_mp3: bool = Field(
        True, description="Convert to MP3 (requires FFmpeg)"
    )


class DownloadVideoRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube video URL")
    format_id: str | None = Field(
        None, description="Specific format ID (e.g. '137+140')"
    )
    resolution: str | None = Field(
        None, description="Preferred resolution (e.g. '1080p', '720p')"
    )


class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: str | None = None
    fps: float | None = None
    vcodec: str | None = None
    acodec: str | None = None
    filesize: int | None = None
    filesize_approx: int | None = None
    tbr: float | None = None
    note: str | None = None


class VideoInfoResponse(BaseModel):
    id: str
    title: str
    duration: int | None = None
    duration_string: str | None = None
    thumbnail: str | None = None
    channel: str | None = None
    uploader: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    upload_date: str | None = None
    description: str | None = None
    webpage_url: str | None = None


class FormatsResponse(BaseModel):
    id: str
    title: str
    formats: list[FormatInfo]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    ffmpeg_available: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None

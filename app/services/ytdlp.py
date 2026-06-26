from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _find_ffmpeg() -> str | None:
    system = shutil.which("ffmpeg")
    if system:
        return os.path.dirname(system)
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            bin_dir = Path(exe).parent / "_compat"
            bin_dir.mkdir(exist_ok=True)
            target = bin_dir / "ffmpeg.exe"
            if not target.exists():
                try:
                    os.link(exe, target)
                except OSError:
                    shutil.copy2(exe, target)
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
            logger.info("FFmpeg found via imageio-ffmpeg at %s", bin_dir)
            return str(bin_dir)
    except ImportError:
        pass
    return None


_find_ffmpeg()


def check_ffmpeg() -> bool:
    return _find_ffmpeg() is not None


class YTDLPService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _base_opts(self) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            "overwrites": True,
            "geo_bypass": True,
            "nocheckcertificate": False,
            "socket_timeout": 60,
            "retries": 10,
            "fragment_retries": 10,
            "extractor_retries": 5,
            "file_access_retries": 5,
        }
        ffmpeg_dir = _find_ffmpeg()
        if ffmpeg_dir:
            opts["ffmpeg_location"] = ffmpeg_dir
        return opts

    def _download_opts(self) -> dict[str, Any]:
        return {
            **self._base_opts(),
            "concurrent_fragment_downloads": 4,
            "extractor_args": {
                "youtube": {"player_client": ["default", "mweb"]},
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
        }

    async def extract_info(self, url: str) -> dict[str, Any]:
        opts = {**self._base_opts(), "skip_download": True}
        return await asyncio.to_thread(self._run_extract, url, opts)

    async def extract_formats(self, url: str) -> dict[str, Any]:
        opts = {**self._base_opts(), "skip_download": True}
        return await asyncio.to_thread(self._run_extract, url, opts)

    async def download_audio(
        self,
        url: str,
        format_id: str | None = None,
        convert_mp3: bool = True,
    ) -> Path:
        output_dir = self.settings.download_path
        tag = f"{int(time.time())}_{id(self)}"

        opts: dict[str, Any] = {
            **self._download_opts(),
            "format": format_id or "ba/b",
            "outtmpl": {"default": f"%(id)s_{tag}_audio.%(ext)s"},
            "paths": {"home": str(output_dir)},
        }

        if convert_mp3 and check_ffmpeg():
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        info = await asyncio.to_thread(self._run_download, url, opts)
        return self._resolve_downloaded_file(info, output_dir, tag)

    async def download_video(
        self,
        url: str,
        format_id: str | None = None,
        resolution: str | None = None,
    ) -> Path:
        output_dir = self.settings.download_path
        tag = f"{int(time.time())}_{id(self)}"
        has_ffmpeg = check_ffmpeg()
        fmt = self._resolve_video_format(format_id, resolution, has_ffmpeg)

        opts: dict[str, Any] = {
            **self._download_opts(),
            "format": fmt,
            "outtmpl": {"default": f"%(id)s_{tag}_video.%(ext)s"},
            "paths": {"home": str(output_dir)},
        }

        if has_ffmpeg:
            opts["merge_output_format"] = "mp4"

        info = await asyncio.to_thread(self._run_download, url, opts)
        return self._resolve_downloaded_file(info, output_dir, tag)

    @staticmethod
    def _resolve_video_format(
        format_id: str | None,
        resolution: str | None,
        has_ffmpeg: bool = True,
    ) -> str:
        if format_id:
            if "+" in format_id:
                return format_id if has_ffmpeg else format_id.split("+")[0]
            return f"{format_id}+ba/b" if has_ffmpeg else format_id

        if has_ffmpeg:
            res_map = {
                "2160p": "bv*[height<=2160]+ba/b[height<=2160]/b[height<=2160]",
                "1440p": "bv*[height<=1440]+ba/b[height<=1440]/b[height<=1440]",
                "1080p": "bv*[height<=1080]+ba/b[height<=1080]/b[height<=1080]",
                "720p": "bv*[height<=720]+ba/b[height<=720]/b[height<=720]",
                "480p": "bv*[height<=480]+ba/b[height<=480]/b[height<=480]",
                "360p": "bv*[height<=360]+ba/b[height<=360]/b[height<=360]",
            }
            default = "bv*+ba/b"
        else:
            res_map = {
                "2160p": "b[height<=2160]/bv*[height<=2160]",
                "1440p": "b[height<=1440]/bv*[height<=1440]",
                "1080p": "b[height<=1080]/bv*[height<=1080]",
                "720p": "b[height<=720]/bv*[height<=720]",
                "480p": "b[height<=480]/bv*[height<=480]",
                "360p": "b[height<=360]/bv*[height<=360]",
            }
            default = "b/bv*"

        if resolution and resolution.lower() in res_map:
            return res_map[resolution.lower()]

        return default

    @staticmethod
    def _run_extract(url: str, opts: dict[str, Any]) -> dict[str, Any]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ValueError("Could not extract info from the given URL")
            return ydl.sanitize_info(info)

    @staticmethod
    def _run_download(url: str, opts: dict[str, Any]) -> dict[str, Any]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise ValueError("Download returned no information")
            return info

    @staticmethod
    def _resolve_downloaded_file(
        info: dict[str, Any], output_dir: Path, tag: str
    ) -> Path:
        downloads = info.get("requested_downloads") or []
        if downloads:
            filepath = downloads[0].get("filepath")
            if filepath:
                p = Path(filepath)
                if p.exists() and p.stat().st_size > 0:
                    return p

        video_id = info.get("id", "unknown")
        best: Path | None = None
        best_mtime = 0.0
        for candidate in output_dir.iterdir():
            if not candidate.is_file():
                continue
            if tag in candidate.name or video_id in candidate.name:
                mt = candidate.stat().st_mtime
                if mt > best_mtime:
                    best = candidate
                    best_mtime = mt
        if best and best.stat().st_size > 0:
            return best

        raise FileNotFoundError(
            f"Downloaded file not found for video {video_id}"
        )

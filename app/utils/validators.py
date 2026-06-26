from __future__ import annotations

import re
from urllib.parse import urlparse

_YOUTUBE_PATTERNS = [
    re.compile(r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}"),
    re.compile(r"^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}"),
    re.compile(r"^(https?://)?youtu\.be/[\w-]{11}"),
    re.compile(r"^(https?://)?(www\.)?youtube\.com/embed/[\w-]{11}"),
    re.compile(r"^(https?://)?music\.youtube\.com/watch\?v=[\w-]{11}"),
]


def is_valid_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https", ""):
        return False
    return any(pattern.match(url) for pattern in _YOUTUBE_PATTERNS)


def sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    sanitized = sanitized.strip(". ")
    return sanitized[:200] if sanitized else "download"

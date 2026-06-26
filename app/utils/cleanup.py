from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


async def schedule_file_deletion(filepath: Path, delay_seconds: float = 30.0) -> None:
    async def _delete() -> None:
        await asyncio.sleep(delay_seconds)
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info("Deleted temporary file: %s", filepath)
        except OSError as e:
            logger.warning("Failed to delete %s: %s", filepath, e)

    asyncio.create_task(_delete())


def cleanup_old_files(directory: Path, max_age_seconds: int) -> int:
    removed = 0
    cutoff = time.time() - max_age_seconds
    if not directory.exists():
        return 0

    for item in directory.iterdir():
        if item.is_file() and item.stat().st_mtime < cutoff:
            try:
                item.unlink()
                removed += 1
                logger.info("Cleaned up stale file: %s", item.name)
            except OSError as e:
                logger.warning("Failed to clean up %s: %s", item.name, e)
    return removed

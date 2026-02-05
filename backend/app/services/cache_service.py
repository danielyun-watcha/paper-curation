"""Cache service for storing API responses locally"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# KST timezone
KST = timezone(timedelta(hours=9))

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'recommendations_cache.json')


class CacheService:
    """Simple JSON file-based cache for API responses"""

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load cache from file"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.info(f"Cache loaded: {len(self._cache)} entries")
            else:
                self._cache = {}
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self._cache = {}

    def _save(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key"""
        entry = self._cache.get(key)
        if entry:
            logger.info(f"Cache hit: {key}")
            return entry.get("data")
        return None

    def set(self, key: str, data: Any):
        """Store value in cache"""
        self._cache[key] = {
            "data": data,
            "cached_at": datetime.now(KST).isoformat()
        }
        self._save()
        logger.info(f"Cache stored: {key}")

    def clear(self):
        """Clear all cache"""
        count = len(self._cache)
        self._cache = {}
        self._save()
        logger.info(f"Cache cleared: {count} entries removed")

    def stats(self) -> dict:
        """Get cache statistics"""
        return {
            "entries": len(self._cache),
            "file": CACHE_FILE,
        }


# Singleton
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


async def start_cache_cleanup_scheduler():
    """Background task: clear cache every Saturday 4:00 AM KST"""
    logger.info("Cache cleanup scheduler started (Saturday 4:00 AM KST)")
    while True:
        now = datetime.now(KST)
        # Calculate next Saturday 4:00 AM KST
        days_until_saturday = (5 - now.weekday()) % 7  # Saturday = 5
        if days_until_saturday == 0 and now.hour >= 4:
            days_until_saturday = 7  # Already past 4 AM on Saturday
        next_saturday = now.replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=days_until_saturday)
        wait_seconds = (next_saturday - now).total_seconds()
        logger.info(f"Next cache cleanup: {next_saturday.isoformat()} (in {wait_seconds/3600:.1f} hours)")
        await asyncio.sleep(wait_seconds)
        get_cache_service().clear()

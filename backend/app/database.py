import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import copy

DATA_FILE = Path(__file__).parent.parent / "data" / "papers.json"

# In-memory cache for database
_cache: Optional[dict] = None
_cache_mtime: Optional[float] = None


def ensure_data_file():
    """Ensure data directory and file exist"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text('{"papers": [], "tags": []}')


def _load_from_file() -> dict:
    """Load data directly from JSON file (bypasses cache)"""
    ensure_data_file()
    return json.loads(DATA_FILE.read_text())


def load_data() -> dict:
    """Load data from JSON file with in-memory caching.

    Returns a deep copy to prevent accidental mutation of cache.
    Cache is invalidated if file mtime changes (external modification).
    """
    global _cache, _cache_mtime

    ensure_data_file()
    current_mtime = DATA_FILE.stat().st_mtime

    # Invalidate cache if file was modified externally
    if _cache is None or _cache_mtime != current_mtime:
        _cache = _load_from_file()
        _cache_mtime = current_mtime

    # Return deep copy to prevent mutation
    return copy.deepcopy(_cache)


def save_data(data: dict):
    """Save data to JSON file and update cache"""
    global _cache, _cache_mtime

    ensure_data_file()
    DATA_FILE.write_text(json.dumps(data, indent=2, default=str))

    # Update cache with saved data
    _cache = copy.deepcopy(data)
    _cache_mtime = DATA_FILE.stat().st_mtime


def invalidate_cache():
    """Manually invalidate the cache (useful for testing)"""
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = None


def generate_id() -> str:
    """Generate a new UUID"""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Get current time in ISO format"""
    return datetime.now().isoformat()

"""
Legacy database utilities.

Note: The main storage has been migrated to SQLite.
This module is kept for backward compatibility with any code
that imports generate_id or now_iso from here.
"""
import uuid
from datetime import datetime


def generate_id() -> str:
    """Generate a new UUID"""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Get current time in ISO format"""
    return datetime.now().isoformat()

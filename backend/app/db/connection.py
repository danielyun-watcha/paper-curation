"""SQLite connection management"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from app.db.schema import SCHEMA_SQL

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / "data" / "papers.db"


def get_connection() -> sqlite3.Connection:
    """Get a new database connection with row factory enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)

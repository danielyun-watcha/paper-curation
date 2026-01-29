import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).parent.parent / "data" / "papers.json"


def ensure_data_file():
    """Ensure data directory and file exist"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text('{"papers": [], "tags": []}')


def load_data() -> dict:
    """Load data from JSON file"""
    ensure_data_file()
    return json.loads(DATA_FILE.read_text())


def save_data(data: dict):
    """Save data to JSON file"""
    ensure_data_file()
    DATA_FILE.write_text(json.dumps(data, indent=2, default=str))


def generate_id() -> str:
    """Generate a new UUID"""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Get current time in ISO format"""
    return datetime.now().isoformat()

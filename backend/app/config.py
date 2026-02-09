from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # Database (SQLite for development, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./paper_curation.db"

    # App
    app_name: str = "Paper Curation API"
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://172.16.20.12:3000"]

    # API Keys
    semantic_scholar_api_key: Optional[str] = None
    deepl_api_key: Optional[str] = None

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()

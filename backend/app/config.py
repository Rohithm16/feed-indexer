"""
App configuration — reads from .env file.
All settings are in one place so they're easy to find and change.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = "sqlite:///./feed_indexer.db"
    fetch_interval_minutes: int = 30
    dedup_window_hours: int = 48
    similarity_threshold: float = 0.35

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single instance used everywhere: from app.config import settings
settings = Settings()

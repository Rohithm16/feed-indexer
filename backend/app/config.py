"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"

    # API / browser integration
    frontend_origin: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Gemini is used only for language generation after local scoring.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_min_importance_score: float = 1.0
    gemini_max_concurrency: int = 2
    gemini_max_retries: int = 3

    # Database
    database_url: str = "sqlite:///./feed_indexer.db"

    # Scheduler / ingestion
    scheduler_enabled: bool = True
    run_startup_ingestion: bool = True
    fetch_interval_minutes: int = 60
    feed_fetch_timeout_seconds: int = 12
    feed_fetch_concurrency: int = 12
    max_article_age_hours: int = 48
    article_retention_hours: int = 72
    dedup_window_hours: int = 48
    similarity_threshold: float = 0.42
    min_event_importance_score: float = 32.0

    # Auth / cookies
    session_secret: str = "dev-only-change-me"
    session_cookie_name: str = "feed_indexer_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # Optional external scheduled trigger protection.
    ingestion_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origin.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
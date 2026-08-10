"""SQLAlchemy database setup and lightweight migrations."""

from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _column_names(table_name: str) -> set[str]:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _json_type() -> str:
    return "TEXT" if engine.dialect.name == "sqlite" else "JSON"


def _add_missing_columns(table_name: str, columns: dict[str, str]) -> None:
    existing = _column_names(table_name)
    if not existing:
        return

    with engine.begin() as connection:
        for name, ddl_type in columns.items():
            if name in existing:
                continue
            logger.info("Adding missing column %s.%s", table_name, name)
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {ddl_type}"))


def _create_index(statement: str) -> None:
    try:
        with engine.begin() as connection:
            connection.execute(text(statement))
    except Exception as exc:
        logger.debug("Skipping index statement %r: %s", statement, exc)


def run_lightweight_migrations() -> None:
    """Patch existing MVP databases without requiring Alembic for this project."""
    _add_missing_columns(
        "articles",
        {
            "normalized_url": "VARCHAR(1000)",
            "publisher_domain": "VARCHAR(255)",
            "source_tier": "INTEGER DEFAULT 2",
            "region": "VARCHAR(100)",
            "language": "VARCHAR(20)",
        },
    )
    _add_missing_columns(
        "events",
        {
            "event_type": "VARCHAR(100)",
            "scope": "VARCHAR(50)",
            "scoring_debug": _json_type(),
            "source_quality_score": "FLOAT DEFAULT 0",
            "publisher_count": "INTEGER DEFAULT 0",
            "summary_generated_at": "DATETIME",
            "summary_version": "INTEGER DEFAULT 1",
            "last_summarized_event_state": "VARCHAR(128)",
        },
    )
    _add_missing_columns("user_preferences", {"user_id": "INTEGER"})

    _create_index("CREATE INDEX IF NOT EXISTS ix_articles_published_at ON articles (published_at)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_articles_event_id ON articles (event_id)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_events_first_seen_at ON events (first_seen_at)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_events_last_updated_at ON events (last_updated_at)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_events_importance_score ON events (importance_score)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    _create_index("CREATE INDEX IF NOT EXISTS ix_user_preferences_user_id ON user_preferences (user_id)")

    if engine.dialect.name == "sqlite":
        _create_index(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_articles_normalized_url "
            "ON articles (normalized_url) WHERE normalized_url IS NOT NULL"
        )
    else:
        _create_index(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_articles_normalized_url "
            "ON articles (normalized_url) WHERE normalized_url IS NOT NULL"
        )


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()

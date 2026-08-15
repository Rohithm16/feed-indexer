"""SQLAlchemy database setup and lightweight migrations."""

from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dimension of the local sentence-transformers embedding used for event
# dedup (all-MiniLM-L6-v2). Keep in sync with deduplication.py's
# _EMBEDDING_DIM and the Column(EmbeddingType(...)) definition on Event.
EMBEDDING_DIM = 384


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


def _ensure_pgvector_extension() -> None:
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as exc:
        logger.warning(
            "Could not create pgvector extension (%s). Embedding-based "
            "dedup candidate retrieval will fail until this is enabled -- "
            "typically requires a superuser role or a managed-Postgres "
            "add-on (e.g. Supabase/RDS both support pgvector but you may "
            "need to enable it from their dashboard rather than SQL).",
            exc,
        )


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
    _ensure_pgvector_extension()

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
            "scoring_debug": "JSON",
            "source_quality_score": "FLOAT DEFAULT 0",
            "publisher_count": "INTEGER DEFAULT 0",
            "summary_generated_at": "TIMESTAMP",
            "summary_version": "INTEGER DEFAULT 1",
            "last_summarized_event_state": "VARCHAR(128)",
            "embedding": f"vector({EMBEDDING_DIM})",
            "article_count": "INTEGER DEFAULT 1",
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
    _create_index(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_articles_normalized_url "
        "ON articles (normalized_url) WHERE normalized_url IS NOT NULL"
    )
    # ANN index for embedding cosine search. Safe to create on an empty or
    # small table -- pgvector just won't get much benefit from it until
    # there's enough data. If the extension isn't enabled yet this is
    # caught and skipped by _create_index rather than blowing up startup.
    _create_index(
        "CREATE INDEX IF NOT EXISTS ix_events_embedding_cosine "
        "ON events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()
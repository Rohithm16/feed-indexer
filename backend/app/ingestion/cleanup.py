"""Retention and cleanup helpers for stale articles and orphaned events."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.article import Article
from app.models.event import Event

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def delete_expired_articles(db: Session) -> int:
    now = _utc_now()
    cutoff = now - timedelta(hours=settings.article_retention_hours)
    expired = (
        db.query(Article)
        .filter(or_(Article.published_at.is_(None), Article.published_at < cutoff))
        .all()
    )
    for article in expired:
        db.delete(article)
    db.flush()
    return len(expired)


def delete_orphaned_events(db: Session) -> int:
    events = db.query(Event).all()
    deleted = 0
    for event in events:
        if not event.articles:
            db.delete(event)
            deleted += 1
    db.flush()
    return deleted


def cleanup_stale_data(db: Session) -> dict[str, int]:
    deleted_articles = delete_expired_articles(db)
    deleted_events = delete_orphaned_events(db)
    return {"expired_articles_deleted": deleted_articles, "orphan_events_deleted": deleted_events}

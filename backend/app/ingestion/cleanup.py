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


def enforce_section_caps(db: Session) -> int:
    """Global storage-level cap enforcement -- keeps only the top-N events
    per section (by importance_score) in the database at all, independent
    of any one user's preferences. This is what actually saves storage and
    Gemini API calls: run this BEFORE the Gemini-analysis pass in the
    pipeline, and events that wouldn't make the cut for their section are
    deleted outright rather than analyzed and stored only to be pushed out
    later. Critical events are exempt -- no cap.
    """
    from app.ranking.ranker import SECTION_CAPS, classify_event_bucket

    events = db.query(Event).filter(Event.title.isnot(None)).all()
    buckets: dict[str, list[Event]] = {}
    for event in events:
        if event.is_critical:
            continue
        buckets.setdefault(classify_event_bucket(event), []).append(event)

    deleted = 0
    for bucket, bucket_events in buckets.items():
        cap = SECTION_CAPS["national"] if bucket.startswith("national:") else SECTION_CAPS.get(bucket, SECTION_CAPS["world"])
        bucket_events.sort(key=lambda e: (e.importance_score or 0), reverse=True)
        for event in bucket_events[cap:]:
            db.delete(event)
            deleted += 1

    db.flush()
    return deleted


def cleanup_stale_data(db: Session) -> dict[str, int]:
    deleted_articles = delete_expired_articles(db)
    deleted_events = delete_orphaned_events(db)
    return {"expired_articles_deleted": deleted_articles, "orphan_events_deleted": deleted_events}
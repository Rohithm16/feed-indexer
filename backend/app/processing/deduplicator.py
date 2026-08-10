"""Event clustering with simple lexical + signal-based matching."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.article import Article
from app.models.event import Event

logger = logging.getLogger(__name__)


def _normalize_words(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _build_text(title: str, description: str | None) -> str:
    parts = [title]
    if description:
        parts.append(description)
    return " ".join(parts)


def _get_recent_events(db: Session) -> list[Event]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.dedup_window_hours)
    return db.query(Event).filter(Event.first_seen_at >= cutoff).all()


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _agreement_score(article: Article, event: Event) -> tuple[float, bool]:
    if not event.title and not event.summary:
        return 0.0, False

    article_text = _build_text(article.title, article.description)
    event_text = _build_text(event.title or "", event.summary or "")
    article_words = _normalize_words(article_text)
    event_words = _normalize_words(event_text)

    common = article_words & event_words
    overlap = len(common) / max(1, len(article_words | event_words))
    title_overlap = 1.0 if article.title and event.title and article.title.lower() in event.title.lower() else 0.0
    category_match = bool(article.category and event.category and article.category == event.category)
    recency = 1.0
    article_time = _normalize_datetime(article.published_at)
    event_time = _normalize_datetime(event.last_updated_at)
    if article_time and event_time:
        age = abs((article_time - event_time).total_seconds()) / 3600
        recency = max(0.0, 1.0 - min(age / 24.0, 1.0))

    score = overlap * 0.6 + title_overlap * 0.2 + recency * 0.1 + (0.1 if category_match else 0.0)
    return score, category_match


def find_matching_event(article: Article, recent_events: list[Event], threshold: float) -> Event | None:
    if not recent_events:
        return None

    best_event: Event | None = None
    best_score = 0.0
    for event in recent_events:
        score, _ = _agreement_score(article, event)
        if score > best_score:
            best_score = score
            best_event = event

    if best_event and best_score >= threshold:
        logger.debug("Matched %s to event %s with score %.2f", article.title[:60], best_event.id, best_score)
        return best_event
    return None


def get_or_create_event(article: Article, db: Session) -> Event:
    recent_events = _get_recent_events(db)
    match = find_matching_event(article, recent_events, settings.similarity_threshold)

    if match:
        match.last_updated_at = datetime.now(timezone.utc)
        return match

    new_event = Event(
        title=article.title,
        category=article.category,
        country=article.country,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
    )
    db.add(new_event)
    db.flush()
    return new_event

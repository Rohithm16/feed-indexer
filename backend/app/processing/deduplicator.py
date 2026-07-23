"""
Deduplicator — groups articles about the same story into Events.

Algorithm:
1. For each new article, build a text representation (title + description).
2. Compare it against recent events using TF-IDF cosine similarity.
3. If similarity > threshold (default 0.35), attach the article to that event.
4. Otherwise, create a new event for the article.

This is intentionally simple and readable. For a larger dataset you'd
move to a proper embedding model (e.g. sentence-transformers), but TF-IDF
works well for news headlines at MVP scale.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.config import settings
from app.models.article import Article
from app.models.event import Event

logger = logging.getLogger(__name__)


def _build_text(title: str, description: Optional[str]) -> str:
    """Combine title and description into a single string for vectorization."""
    parts = [title]
    if description:
        parts.append(description)
    return " ".join(parts)


def _get_recent_events(db: Session) -> list[Event]:
    """
    Load events from the last N hours.
    We only cluster against recent events to avoid false positives
    between old and new stories on similar topics.
    """
    cutoff = datetime.utcnow() - timedelta(hours=settings.dedup_window_hours)
    return (
        db.query(Event)
        .filter(Event.first_seen_at >= cutoff)
        .all()
    )


def find_matching_event(
    article: Article,
    recent_events: list[Event],
    threshold: float,
) -> Optional[Event]:
    """
    Find an existing event that this article belongs to.
    Returns the best matching event, or None if no match above threshold.
    """
    if not recent_events:
        return None

    article_text = _build_text(article.title, article.description)

    # Build corpus: article text + each event's title
    event_texts = [
        _build_text(e.title or "", e.summary or "")
        for e in recent_events
    ]
    corpus = [article_text] + event_texts

    # Vectorize and compute similarities
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        # Compare article (row 0) against all events (rows 1+)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    except ValueError:
        # Can happen if all texts are empty after stop-word removal
        return None

    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score >= threshold:
        logger.debug(
            f"Matched '{article.title[:60]}' → event {recent_events[best_idx].id} "
            f"(similarity={best_score:.2f})"
        )
        return recent_events[best_idx]

    return None


def get_or_create_event(article: Article, db: Session) -> Event:
    """
    Main entry point for deduplication.
    Given an article, either find its event or create a new one.
    """
    recent_events = _get_recent_events(db)
    match = find_matching_event(article, recent_events, settings.similarity_threshold)

    if match:
        # Update timestamp so this event bubbles up in recency sorting
        match.last_updated_at = datetime.utcnow()
        return match

    # No match — create a fresh event seeded with basic info from the article
    new_event = Event(
        title=article.title,           # will be replaced by Gemini analysis
        category=article.category,
        country=article.country,
        first_seen_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow(),
    )
    db.add(new_event)
    db.flush()  # get the new event ID without committing
    return new_event

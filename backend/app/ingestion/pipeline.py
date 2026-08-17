"""Ingestion pipeline with freshness gates, cleanup, and local scoring."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.ai.gemini import analyze_event, apply_analysis_to_event
from app.config import settings
from app.database import SessionLocal
from app.ingestion.cleanup import cleanup_stale_data, enforce_section_caps
from app.ingestion.fetcher import fetch_all_feeds
from app.ingestion.normalizer import normalize_feed_entries
from app.models.article import Article
from app.models.event import Event
from app.processing.deduplicator import get_or_create_event
from app.ranking.scorer import apply_scoring_to_event, is_low_editorial_content

logger = logging.getLogger(__name__)


def _is_low_value(title: str, description: str | None) -> bool:
    return is_low_editorial_content(title, description)


def _is_stale(article: Article) -> bool:
    if article.published_at is None:
        return True
    now = datetime.now(timezone.utc)
    if article.published_at.tzinfo is None:
        article.published_at = article.published_at.replace(tzinfo=timezone.utc)
    age_hours = (now - article.published_at.astimezone(timezone.utc)).total_seconds() / 3600.0
    return age_hours > settings.max_article_age_hours


def _event_state_hash(event: Event) -> str:
    payload = f"{event.id}:{event.importance_score:.2f}:{len(event.articles or [])}:{event.last_updated_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


async def run_ingestion() -> dict:
    logger.info("Starting ingestion run")
    start = datetime.now(timezone.utc)

    db: Session = SessionLocal()
    stats = {
        "feeds_checked": 0,
        "feeds_failed": 0,
        "entries_seen": 0,
        "stale_skipped": 0,
        "low_value_skipped": 0,
        "duplicate_skipped": 0,
        "new_articles": 0,
        "new_events": 0,
        "merged_events": 0,
        "important_events": 0,
        "events_evicted": 0,
        "gemini_calls": 0,
        "gemini_failures": 0,
    }
    changed_event_ids: set[int] = set()

    existing_normalized_urls = {
        url for (url,) in db.query(Article.normalized_url).filter(Article.normalized_url.isnot(None)).all() if url
    }
    existing_urls = {url for (url,) in db.query(Article.url).all() if url}
    seen_urls: set[str] = set()

    try:
        feed_results = await fetch_all_feeds()
        stats["feeds_checked"] = len(feed_results)
        for feed, entries in feed_results:
            if not entries:
                continue
            stats["entries_seen"] += len(entries)
            articles = normalize_feed_entries(feed, entries)
            for article in articles:
                normalized_url = article.normalized_url or article.url
                if normalized_url in seen_urls or normalized_url in existing_normalized_urls or article.url in existing_urls:
                    stats["duplicate_skipped"] += 1
                    continue
                seen_urls.add(normalized_url)

                if _is_stale(article):
                    stats["stale_skipped"] += 1
                    continue

                if _is_low_value(article.title, article.description):
                    stats["low_value_skipped"] += 1
                    continue

                event = get_or_create_event(article, db)
                if event.id is not None and event.id not in changed_event_ids:
                    changed_event_ids.add(event.id)
                article.event_id = event.id
                db.add(article)
                stats["new_articles"] += 1

                if (event.article_count or 1) <= 1:
                    stats["new_events"] += 1
                else:
                    stats["merged_events"] += 1

            db.flush()

        db.commit()

        for event_id in changed_event_ids:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                continue
            apply_scoring_to_event(event, list(event.articles or []))
            db.add(event)
        db.commit()

        stats["events_evicted"] = enforce_section_caps(db)
        db.commit()

        for event_id in changed_event_ids:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                # Evicted by section-cap enforcement above -- skips the
                # Gemini call entirely rather than analyzing an event that
                # was just deleted for not making the cut.
                continue
            if event.importance_score >= settings.gemini_min_importance_score:
                stats["important_events"] += 1
                state_hash = _event_state_hash(event)
                if event.summary is None or event.summary_generated_at is None or event.last_summarized_event_state != state_hash:
                    stats["gemini_calls"] += 1
                    analysis = analyze_event(list(event.articles or []))
                    if analysis:
                        apply_analysis_to_event(event, analysis)
                        event.summary_generated_at = datetime.now(timezone.utc)
                        event.summary_version = (event.summary_version or 1) + 1
                        event.last_summarized_event_state = state_hash
                        db.add(event)
                    else:
                        stats["gemini_failures"] += 1
            db.add(event)

        cleanup_stats = cleanup_stale_data(db)
        stats.update(cleanup_stats)
        db.commit()

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        summary = {
            "status": "ok",
            **stats,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info("Ingestion complete: %s", summary)
        return summary
    except Exception as exc:
        db.rollback()
        logger.exception("Ingestion failed")
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()
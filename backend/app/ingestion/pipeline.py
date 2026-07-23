"""
Ingestion pipeline — orchestrates the full fetch → normalize → deduplicate → AI analyze flow.

This is the main entry point called by the scheduler and the manual /api/ingest endpoint.
Each step is clearly separated and logged so it's easy to debug.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.ingestion.fetcher import fetch_all_feeds
from app.ingestion.normalizer import normalize_feed_entries
from app.processing.deduplicator import get_or_create_event
from app.ai.gemini import analyze_event, apply_analysis_to_event
from app.models.article import Article
from app.models.event import Event

logger = logging.getLogger(__name__)


async def run_ingestion() -> dict:
    """
    Full ingestion pipeline:
    1. Fetch all RSS feeds
    2. Normalize entries into Articles
    3. Deduplicate / cluster into Events
    4. Run Gemini analysis on events that changed
    5. Commit everything to the database

    Returns a summary dict with counts for monitoring.
    """
    logger.info("Starting ingestion run")
    start = datetime.utcnow()

    db: Session = SessionLocal()
    new_articles = 0
    new_events = 0
    updated_events = 0
    events_to_analyze = set()  # event IDs that got new articles
    # Load all existing article URLs once (avoids one DB query per article)
    existing_urls = {
        url
        for (url,) in db.query(Article.url).all()
    }

    # Track duplicates encountered during this ingestion run
    seen_urls = set()


    try:
        # ── Step 1: Fetch ────────────────────────────────────────────────────
        feed_results = await fetch_all_feeds()
        logger.info(f"Fetched {len(feed_results)} feeds")

        # ── Step 2 & 3: Normalize + Deduplicate ─────────────────────────────
        for feed, entries in feed_results:
            articles = normalize_feed_entries(feed, entries)

            for article in articles:
                # Duplicate within this ingestion run
                if article.url in seen_urls:
                    continue

                # Already stored in the database
                if article.url in existing_urls:
                    continue

                seen_urls.add(article.url)

                # Find or create matching event
                event = get_or_create_event(article, db)

                is_new_event = (
                    event.first_seen_at == event.last_updated_at
                )

                article.event_id = event.id

                logger.info(f"Adding article: {article.url}")

                db.add(article)
                new_articles += 1

                if is_new_event:
                    new_events += 1
                else:
                    updated_events += 1

                events_to_analyze.add(event.id)

        db.commit()
        logger.info(f"Saved {new_articles} new articles, {new_events} new events")

        # ── Step 4: AI Analysis ──────────────────────────────────────────────
        # Re-analyze events that received new articles in this run

        analyzed = 0
        for event_id in events_to_analyze:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                continue

            analysis = analyze_event(event.articles)
            if analysis:
                apply_analysis_to_event(event, analysis)
                db.add(event)
                analyzed += 1

        db.commit()

        elapsed = (datetime.utcnow() - start).total_seconds()
        summary = {
            "status": "ok",
            "new_articles": new_articles,
            "new_events": new_events,
            "updated_events": updated_events,
            "events_analyzed": analyzed,
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(f"Ingestion complete: {summary}")
        return summary

    except Exception as exc:
        db.rollback()
        logger.exception(f"Ingestion failed: {exc}")
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()

"""
Scheduler — runs the ingestion pipeline on a timer using APScheduler.

Configured via FETCH_INTERVAL_MINUTES in .env (default: 30 minutes).
Also provides a manual trigger endpoint.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.ingestion.pipeline import run_ingestion

logger = logging.getLogger(__name__)

# Single scheduler instance shared by the whole app
scheduler = AsyncIOScheduler()


def _run_ingestion_sync():
    """
    APScheduler calls synchronous functions. We bridge to async here.
    """
    asyncio.get_event_loop().run_until_complete(run_ingestion())


async def start_scheduler():
    """
    Start the background scheduler. Called once at app startup.
    Triggers an immediate ingestion run, then repeats on the interval.
    """
    interval = settings.fetch_interval_minutes

    scheduler.add_job(
        run_ingestion,
        trigger="interval",
        minutes=interval,
        id="ingestion",
        replace_existing=True,
        coalesce=True,        # skip if a previous run is still going
        max_instances=1,      # never run two ingestions at once
    )

    scheduler.start()
    logger.info(f"Scheduler started — will ingest every {interval} minutes")

    # Run once immediately at startup so the feed is populated right away
    logger.info("Running initial ingestion on startup...")
    try:
        await run_ingestion()
    except Exception as exc:
        logger.error(f"Initial ingestion failed: {exc}")


def stop_scheduler():
    """Stop the scheduler cleanly on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

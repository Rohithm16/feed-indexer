"""
RSS fetcher — fetches all registered RSS feeds and returns raw parsed entries.

Uses feedparser (synchronous) inside a thread pool so it doesn't block
the async event loop. Each feed is fetched independently so one slow or
broken feed doesn't block the others.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import feedparser

from app.providers.base import FeedInfo
from app.providers.registry import get_all_feeds

logger = logging.getLogger(__name__)

# Thread pool for running blocking feedparser calls
_executor = ThreadPoolExecutor(max_workers=10)


def _fetch_one(feed: FeedInfo) -> Tuple[FeedInfo, list]:
    """
    Fetch a single RSS feed. Returns (feed_info, list_of_entries).
    Runs in a thread so it doesn't block the event loop.
    """
    try:
        parsed = feedparser.parse(feed.url)
        entries = parsed.get("entries", [])
        logger.info(f"Fetched {len(entries)} entries from {feed.name}")
        return feed, entries
    except Exception as exc:
        logger.error(f"Failed to fetch {feed.name} ({feed.url}): {exc}")
        return feed, []


async def fetch_all_feeds() -> List[Tuple[FeedInfo, list]]:
    """
    Fetch every registered RSS feed concurrently.
    Returns a list of (FeedInfo, entries) tuples.
    """
    feeds = get_all_feeds()
    loop = asyncio.get_event_loop()

    # Run all fetches in parallel using the thread pool
    tasks = [
        loop.run_in_executor(_executor, _fetch_one, feed)
        for feed in feeds
    ]
    results = await asyncio.gather(*tasks)
    return list(results)


async def fetch_feeds_for_providers(provider_names: List[str]) -> List[Tuple[FeedInfo, list]]:
    """
    Fetch only feeds belonging to specific providers.
    Useful for re-fetching a subset of sources.
    """
    feeds = [f for f in get_all_feeds() if f.name in provider_names]
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(_executor, _fetch_one, feed) for feed in feeds]
    results = await asyncio.gather(*tasks)
    return list(results)

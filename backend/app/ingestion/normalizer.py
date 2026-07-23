"""
Normalizer — converts raw feedparser entries into clean Article objects.

Different RSS feeds use slightly different field names and date formats.
This module smooths over those differences so the rest of the app works
with a single consistent Article structure.
"""

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from app.models.article import Article
from app.providers.base import FeedInfo

logger = logging.getLogger(__name__)


def _parse_date(entry: dict) -> Optional[datetime]:
    """
    Try to parse a publication date from a feedparser entry.
    feedparser provides `published_parsed` (a time.struct_time) when it can.
    """
    # feedparser's parsed struct_time is the most reliable
    if entry.get("published_parsed"):
        try:
            return datetime(*entry["published_parsed"][:6])
        except Exception:
            pass

    # Fallback: parse the raw string
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            return parsedate_to_datetime(raw).replace(tzinfo=None)
        except Exception:
            pass

    return None


def _clean_text(text: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Strip whitespace and truncate to a safe length."""
    if not text:
        return None
    cleaned = " ".join(text.split())  # collapse all whitespace
    return cleaned[:max_length] if len(cleaned) > max_length else cleaned


def normalize_entry(entry: dict, feed: FeedInfo) -> Optional[Article]:
    """
    Convert a single feedparser entry into an Article model instance.
    Returns None if the entry doesn't have the minimum required fields.
    """
    # URL is required — skip entries without one
    url = entry.get("link") or entry.get("id")
    if not url:
        return None

    # Title is required
    title = _clean_text(entry.get("title"))
    if not title:
        return None

    # Description: try summary, then content, then nothing
    description = None
    if entry.get("summary"):
        description = _clean_text(entry["summary"], max_length=500)
    elif entry.get("content"):
        # content is a list of dicts
        try:
            description = _clean_text(entry["content"][0].get("value", ""), max_length=500)
        except (IndexError, KeyError):
            pass

    return Article(
        title=title,
        description=description,
        url=url,
        published_at=_parse_date(entry),
        source_name=feed.name,
        source_url=feed.url,
        category=feed.category,
        country=feed.country,
    )


def normalize_feed_entries(feed: FeedInfo, entries: list) -> list[Article]:
    """
    Normalize all entries from one feed. Skips malformed entries with a warning.
    """
    articles = []
    for entry in entries:
        try:
            article = normalize_entry(entry, feed)
            if article:
                articles.append(article)
        except Exception as exc:
            logger.warning(f"Skipping malformed entry from {feed.name}: {exc}")
    return articles

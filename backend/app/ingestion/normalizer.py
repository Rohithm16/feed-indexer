"""Normalizer — converts raw feedparser entries into clean Article objects."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.models.article import Article
from app.providers.base import FeedInfo

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for key in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid", "fbclid"]:
        query.pop(key, None)
    rebuilt = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query, doseq=True), ""))
    return rebuilt.strip()


def _parse_date(entry: dict[str, Any]) -> datetime | None:
    if entry.get("published_parsed"):
        try:
            parsed = entry["published_parsed"]
            value = datetime(*parsed[:6])
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        except Exception:
            pass

    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed is None:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            pass

    return None


def _clean_text(text: str | None, max_length: int = 1000) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:max_length] if len(cleaned) > max_length else cleaned


def normalize_entry(entry: dict[str, Any], feed: FeedInfo) -> Article | None:
    url = entry.get("link") or entry.get("id")
    if not url:
        return None

    title = _clean_text(entry.get("title"))
    if not title:
        return None

    description = None
    if entry.get("summary"):
        description = _clean_text(entry["summary"], max_length=500)
    elif entry.get("content"):
        try:
            description = _clean_text(entry["content"][0].get("value", ""), max_length=500)
        except (IndexError, KeyError):
            pass

    return Article(
        title=title,
        description=description,
        url=url,
        normalized_url=_normalize_url(url),
        published_at=_parse_date(entry),
        source_name=feed.name,
        source_url=feed.url,
        category=feed.category,
        country=feed.country,
        source_tier=feed.tier,
        publisher_domain=feed.url.split("//")[-1].split("/")[0] if feed.url else None,
    )


def normalize_feed_entries(feed: FeedInfo, entries: list[dict[str, Any]]) -> list[Article]:
    articles: list[Article] = []
    for entry in entries:
        try:
            article = normalize_entry(entry, feed)
            if article:
                articles.append(article)
        except Exception as exc:
            logger.warning("Skipping malformed entry from %s: %s", feed.name, exc)
    return articles
"""
Provider registry — the single place that lists all active providers.

To add a new provider:
1. Create a file in app/providers/feeds/
2. Add it to the PROVIDERS list below.
"""

from typing import List

from app.providers.base import NewsProvider, FeedInfo
from app.providers.feeds.bbc import BBCProvider
from app.providers.feeds.reuters import ReutersProvider
from app.providers.feeds.ap_news import APNewsProvider
from app.providers.feeds.world import TheGuardianProvider, AlJazeeraProvider, NPRProvider
from app.providers.feeds.technology import (
    ArsTechnicaProvider,
    HackerNewsProvider,
    TechCrunchProvider,
    WiredProvider,
    TheVergeProvider,
)
from app.providers.feeds.business_science import (
    CNBCProvider,
    NatureProvider,
    NewScientistProvider,
    NASAProvider,
)

# ── Add new providers here ───────────────────────────────────────────────────
PROVIDERS: List[NewsProvider] = [
    BBCProvider(),
    ReutersProvider(),
    APNewsProvider(),
    TheGuardianProvider(),
    AlJazeeraProvider(),
    NPRProvider(),
    ArsTechnicaProvider(),
    HackerNewsProvider(),
    TechCrunchProvider(),
    WiredProvider(),
    TheVergeProvider(),
    CNBCProvider(),
    NatureProvider(),
    NewScientistProvider(),
    NASAProvider(),
]


def get_all_providers() -> List[NewsProvider]:
    """Return every registered provider."""
    return PROVIDERS


def get_all_feeds() -> List[FeedInfo]:
    """Return every RSS feed from every registered provider."""
    feeds = []
    for provider in PROVIDERS:
        for feed in provider.feeds:
            feeds.append(feed)
    return feeds


def get_provider_names() -> List[str]:
    """Return list of provider display names (used in settings UI)."""
    return [p.name for p in PROVIDERS]


def get_feed_by_url(url: str) -> FeedInfo | None:
    """Look up a FeedInfo by its RSS URL."""
    for feed in get_all_feeds():
        if feed.url == url:
            return feed
    return None

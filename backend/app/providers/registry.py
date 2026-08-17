"""
Provider registry — the single place that lists all active providers.

To add a new provider:
1. Create a file in app/providers/feeds/
2. Add it to the PROVIDERS list below.
"""

from typing import List

from app.providers.base import NewsProvider, FeedInfo
from app.providers.feeds.bbc import BBCProvider
from app.providers.feeds.ap_news import APNewsProvider
from app.providers.feeds.world import TheGuardianProvider, NPRProvider
from app.providers.feeds.india import TheHinduProvider, TimesOfIndiaProvider
from app.providers.feeds.international import PBSNewsHourProvider, DWProvider
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
# Reuters removed: feeds.reuters.com was discontinued by Reuters back in
# 2020 and has returned 404s/redirects ever since -- these 4 feeds were
# dead the entire time, silently failing on every ingestion run.
# Al Jazeera removed: its only public feed is an unfiltered firehose
# (sports, culture, opinion all mixed into "world" news) -- see the note
# in providers/feeds/world.py.
# PBS NewsHour and DW added to backfill the general-coverage gap left by
# removing those two.
PROVIDERS: List[NewsProvider] = [
    BBCProvider(),
    APNewsProvider(),
    TheGuardianProvider(),
    NPRProvider(),
    TheHinduProvider(),
    TimesOfIndiaProvider(),
    PBSNewsHourProvider(),
    DWProvider(),
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
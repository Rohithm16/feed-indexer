from app.providers.base import NewsProvider, FeedInfo
from typing import List


class ArsTechnicaProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Ars Technica"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Ars Technica",
                url="http://feeds.arstechnica.com/arstechnica/index",
                category="technology",
                country="world",
                tier=2,
            ),
        ]


class HackerNewsProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Hacker News"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            # Tier 3: crowd-voted link aggregator, not a newsroom. Real
            # signal for tech-industry discussion but a different kind of
            # source than the rest of this list -- kept lower tier so it
            # doesn't get treated as equally authoritative as an outlet
            # with actual reporters and editorial review.
            FeedInfo(
                name="Hacker News Top",
                url="https://hnrss.org/frontpage",
                category="technology",
                country="world",
                tier=3,
            ),
        ]


class TechCrunchProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "TechCrunch"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="TechCrunch",
                url="https://techcrunch.com/feed/",
                category="technology",
                country="world",
                tier=2,
            ),
        ]


class WiredProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Wired"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Wired",
                url="https://www.wired.com/feed/rss",
                category="technology",
                country="world",
                tier=2,
            ),
        ]


class TheVergeProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "The Verge"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="The Verge",
                url="https://www.theverge.com/rss/index.xml",
                category="technology",
                country="world",
                tier=2,
            ),
        ]
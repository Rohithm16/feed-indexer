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
            ),
        ]


class HackerNewsProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Hacker News"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Hacker News Top",
                url="https://hnrss.org/frontpage",
                category="technology",
                country="world",
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
            ),
        ]

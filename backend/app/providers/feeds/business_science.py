from app.providers.base import NewsProvider, FeedInfo
from typing import List


class CNBCProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "CNBC"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="CNBC Top News",
                url="https://www.cnbc.com/id/100003114/device/rss/rss.html",
                category="business",
                country="us",
                tier=2,
            ),
            FeedInfo(
                name="CNBC Finance",
                url="https://www.cnbc.com/id/10000664/device/rss/rss.html",
                category="finance",
                country="us",
                tier=2,
            ),
            FeedInfo(
                name="CNBC Technology",
                url="https://www.cnbc.com/id/19854910/device/rss/rss.html",
                category="technology",
                country="us",
                tier=2,
            ),
        ]


class NatureProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Nature"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Nature News",
                url="https://www.nature.com/nature.rss",
                category="science",
                country="world",
                tier=1,
            ),
        ]


class NewScientistProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "New Scientist"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="New Scientist",
                url="https://www.newscientist.com/feed/home/",
                category="science",
                country="world",
                tier=2,
            ),
        ]


class NASAProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "NASA"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            # Tier 1: primary source / official agency releases, not
            # third-party reporting.
            FeedInfo(
                name="NASA Breaking News",
                url="https://www.nasa.gov/rss/dyn/breaking_news.rss",
                category="science",
                country="us",
                tier=1,
            ),
        ]
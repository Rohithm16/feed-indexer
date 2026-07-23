from app.providers.base import NewsProvider, FeedInfo
from typing import List


class TheGuardianProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "The Guardian"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="The Guardian World",
                url="https://www.theguardian.com/world/rss",
                category="world",
                country="world",
            ),
            FeedInfo(
                name="The Guardian Technology",
                url="https://www.theguardian.com/uk/technology/rss",
                category="technology",
                country="world",
            ),
            FeedInfo(
                name="The Guardian Science",
                url="https://www.theguardian.com/science/rss",
                category="science",
                country="world",
            ),
            FeedInfo(
                name="The Guardian Business",
                url="https://www.theguardian.com/business/rss",
                category="business",
                country="world",
            ),
        ]


class AlJazeeraProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Al Jazeera"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Al Jazeera English",
                url="https://www.aljazeera.com/xml/rss/all.xml",
                category="world",
                country="world",
            ),
        ]


class NPRProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "NPR"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="NPR Top Stories",
                url="https://feeds.npr.org/1001/rss.xml",
                category="national",
                country="us",
            ),
            FeedInfo(
                name="NPR Science",
                url="https://feeds.npr.org/1007/rss.xml",
                category="science",
                country="us",
            ),
            FeedInfo(
                name="NPR Health",
                url="https://feeds.npr.org/1128/rss.xml",
                category="health",
                country="us",
            ),
        ]

from app.providers.base import NewsProvider, FeedInfo
from typing import List


class ReutersProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Reuters"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Reuters World News",
                url="https://feeds.reuters.com/reuters/worldNews",
                category="world",
                country="world",
            ),
            FeedInfo(
                name="Reuters Business",
                url="https://feeds.reuters.com/reuters/businessNews",
                category="business",
                country="world",
            ),
            FeedInfo(
                name="Reuters Technology",
                url="https://feeds.reuters.com/reuters/technologyNews",
                category="technology",
                country="world",
            ),
            FeedInfo(
                name="Reuters US News",
                url="https://feeds.reuters.com/Reuters/domesticNews",
                category="national",
                country="us",
            ),
        ]

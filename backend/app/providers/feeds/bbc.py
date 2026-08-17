from app.providers.base import NewsProvider, FeedInfo
from typing import List


class BBCProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "BBC"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="BBC World News",
                url="http://feeds.bbci.co.uk/news/world/rss.xml",
                category="world",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="BBC Technology",
                url="http://feeds.bbci.co.uk/news/technology/rss.xml",
                category="technology",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="BBC Business",
                url="http://feeds.bbci.co.uk/news/business/rss.xml",
                category="business",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="BBC Science & Environment",
                url="http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                category="science",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="BBC US & Canada",
                url="http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
                category="national",
                country="us",
                tier=1,
            ),
        ]
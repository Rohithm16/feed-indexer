from app.providers.base import NewsProvider, FeedInfo
from typing import List


class APNewsProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "AP News"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="AP Top News",
                url="https://feeds.apnews.com/rss/apf-topnews",
                category="world",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="AP US News",
                url="https://feeds.apnews.com/rss/apf-usnews",
                category="national",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="AP Technology",
                url="https://feeds.apnews.com/rss/apf-technology",
                category="technology",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="AP Science",
                url="https://feeds.apnews.com/rss/apf-science",
                category="science",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="AP Politics",
                url="https://feeds.apnews.com/rss/apf-politics",
                category="politics",
                country="us",
                tier=1,
            ),
        ]
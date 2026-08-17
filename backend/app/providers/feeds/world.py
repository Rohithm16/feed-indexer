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
                tier=1,
            ),
            FeedInfo(
                name="The Guardian Technology",
                url="https://www.theguardian.com/uk/technology/rss",
                category="technology",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="The Guardian Science",
                url="https://www.theguardian.com/science/rss",
                category="science",
                country="world",
                tier=1,
            ),
            FeedInfo(
                name="The Guardian Business",
                url="https://www.theguardian.com/business/rss",
                category="business",
                country="world",
                tier=1,
            ),
        ]


# AlJazeeraProvider intentionally removed. Al Jazeera's only public RSS
# feed (aljazeera.com/xml/rss/all.xml) is a firehose of literally
# everything the site publishes -- sports scores, culture pieces, and
# opinion columns mixed in with hard news, all tagged "world" regardless
# of content. That's the direct cause of items like "Al Jazeera
# journalist opens beach cafe" showing up as World news: not a scoring
# failure, just an unfiltered feed. No narrower official section feed
# was found (checked as of Aug 2026) -- if Al Jazeera adds one later,
# it's a straightforward FeedInfo addition here.


class NPRProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "NPR"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            # NPR's old "Top Stories" feed (id 1001) is a general firehose
            # like Al Jazeera's -- includes lifestyle/wellness pieces
            # ("5 exercises that can prevent pregnancy pain") tagged
            # "national" regardless of content. Replaced with NPR's actual
            # topic-specific feeds, which are properly narrow.
            FeedInfo(
                name="NPR World",
                url="https://feeds.npr.org/1004/rss.xml",
                category="world",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="NPR Business",
                url="https://feeds.npr.org/1006/rss.xml",
                category="business",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="NPR Politics",
                url="https://feeds.npr.org/1014/rss.xml",
                category="politics",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="NPR Science",
                url="https://feeds.npr.org/1007/rss.xml",
                category="science",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="NPR Health",
                url="https://feeds.npr.org/1128/rss.xml",
                category="health",
                country="us",
                tier=1,
            ),
        ]
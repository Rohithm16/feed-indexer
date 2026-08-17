"""India sources. The Hindu's feeder-pattern feeds are narrow and serious
(comparable to Guardian/NPR's topic feeds elsewhere in this registry).
Times of India's top-stories feed is well-established but more general --
kept at tier 2 and worth monitoring for the same "firehose" leakage
problem that got NPR/Al Jazeera trimmed, since it isn't a narrow topic
feed. Country is intentionally "in" on every feed here: national-country
routing takes priority over content-type routing (see ranker.py), so a
Hindu Sci-Tech story about India still correctly lands in the India
National sub-feed rather than Tech & Science.
"""

from app.providers.base import NewsProvider, FeedInfo
from typing import List


class TheHinduProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "The Hindu"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="The Hindu National",
                url="https://www.thehindu.com/news/national/feeder/default.rss",
                category="national",
                country="in",
                tier=1,
            ),
            FeedInfo(
                name="The Hindu Business",
                url="https://www.thehindu.com/business/feeder/default.rss",
                category="business",
                country="in",
                tier=1,
            ),
            FeedInfo(
                name="The Hindu Sci-Tech",
                url="https://www.thehindu.com/sci-tech/feeder/default.rss",
                category="technology",
                country="in",
                tier=1,
            ),
        ]


class TimesOfIndiaProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "Times of India"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="Times of India Top Stories",
                url="https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                category="national",
                country="in",
                tier=2,
            ),
        ]
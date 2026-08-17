"""PBS NewsHour and Deutsche Welle -- added to backfill general world/national
coverage after removing Reuters (dead feeds, see reuters.py) and Al
Jazeera's firehose (see world.py). Both are nonprofit/public-service
broadcasters with narrow, well-behaved topic feeds and minimal
sensationalism, which is exactly the profile that was missing.
"""

from app.providers.base import NewsProvider, FeedInfo
from typing import List


class PBSNewsHourProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "PBS NewsHour"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            FeedInfo(
                name="PBS NewsHour Nation",
                url="https://www.pbs.org/newshour/feeds/rss/nation",
                category="national",
                country="us",
                tier=1,
            ),
            FeedInfo(
                name="PBS NewsHour World",
                url="https://www.pbs.org/newshour/feeds/rss/world",
                category="world",
                country="world",
                tier=1,
            ),
        ]


class DWProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "DW"

    @property
    def feeds(self) -> List[FeedInfo]:
        return [
            # rss-en-top, not the broader rss-en-all -- the "all" variant
            # explicitly advertises "off-beat stories" mixed in, same
            # problem class as Al Jazeera's all.xml.
            FeedInfo(
                name="DW Top Stories",
                url="https://rss.dw.com/rdf/rss-en-top",
                category="world",
                country="world",
                tier=1,
            ),
        ]
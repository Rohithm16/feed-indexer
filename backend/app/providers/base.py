"""
Base class for all news providers.

To add a new RSS source:
1. Create a new file in app/providers/feeds/
2. Define a class that inherits from NewsProvider
3. Implement `name` and `feeds`
4. Register it in app/providers/registry.py

That's it — the ingestion pipeline picks it up automatically.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class FeedInfo:
    """
    Describes a single RSS feed.
    
    - name: display name for the feed (e.g. "BBC World News")
    - url: the RSS feed URL
    - category: which section this belongs to (world/technology/business/science/national/health/politics)
    - country: "us", "uk", "in", "world", etc.
    """
    name: str
    url: str
    category: str
    country: str = "world"


class NewsProvider(ABC):
    """
    Abstract base for all news providers.
    Each provider represents one publication or data source.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short name used as source_name on articles, e.g. 'BBC'."""
        pass

    @property
    @abstractmethod
    def feeds(self) -> List[FeedInfo]:
        """All RSS feeds offered by this provider."""
        pass

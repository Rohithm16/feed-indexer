"""
Pydantic schemas for Event API responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.schemas.article import ArticleOut


class EventCard(BaseModel):
    """
    Compact event representation used on the homepage feed.
    Includes just enough to render an event card.
    """
    id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    importance_score: float = 0.0
    is_critical: bool = False
    source_count: int = 0           # number of articles covering this event
    first_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None

    # Personalization transparency — why is this event shown?
    recommendation_reason: Optional[str] = None

    # Representative article (for "Read original" button on card)
    primary_source_name: Optional[str] = None
    primary_source_url: Optional[str] = None

    model_config = {"from_attributes": True}


class EventDetail(EventCard):
    """
    Full event detail — includes all articles. Used on the event detail page.
    """
    articles: List[ArticleOut] = []


class SectionedFeed(BaseModel):
    """
    The full homepage feed, organized into named sections.
    Each section is a list of EventCard items.
    Sections with no events are omitted from the response.
    """
    critical: List[EventCard] = []
    local: List[EventCard] = []
    national: List[EventCard] = []
    world: List[EventCard] = []
    technology: List[EventCard] = []
    business: List[EventCard] = []
    science: List[EventCard] = []

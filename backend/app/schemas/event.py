"""
Pydantic schemas for Event API responses.
"""

from datetime import datetime
from typing import Dict, Optional, List
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
    country: Optional[str] = None   # for flag display on national cards
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
    National is grouped by country code (e.g. "in", "us") since a user
    can select one or both -- each gets its own capped sub-feed. All
    other sections are flat, capped lists ordered by importance.
    """
    critical: List[EventCard] = []
    national: Dict[str, List[EventCard]] = {}
    world: List[EventCard] = []
    tech_science: List[EventCard] = []
    business_finance: List[EventCard] = []
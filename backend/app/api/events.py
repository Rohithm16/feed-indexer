"""
Events API — the main data endpoints for the frontend.

GET /api/events          → sectioned homepage feed
GET /api/events/{id}     → full event detail with all articles
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.user_prefs import UserPreferences
from app.ranking.ranker import section_events
from app.schemas.event import EventCard, EventDetail, SectionedFeed
from app.schemas.article import ArticleOut

router = APIRouter(prefix="/api/events", tags=["events"])
logger = logging.getLogger(__name__)


def _get_preferences(db: Session) -> Optional[UserPreferences]:
    """Get the single user's preferences row, or None if not set."""
    return db.query(UserPreferences).first()


def _event_to_card(event: Event, reason: str = "") -> EventCard:
    """Convert an Event model to an EventCard schema."""
    # Pick the earliest/most prominent article as the primary source
    primary = None
    if event.articles:
        primary = sorted(
            event.articles,
            key=lambda a: a.published_at or datetime.min,
        )[0]

    return EventCard(
        id=event.id,
        title=event.title,
        summary=event.summary,
        why_it_matters=event.why_it_matters,
        category=event.category,
        tags=event.tags or [],
        importance_score=event.importance_score or 0.0,
        is_critical=event.is_critical or False,
        source_count=len(event.articles),
        first_seen_at=event.first_seen_at,
        last_updated_at=event.last_updated_at,
        recommendation_reason=reason,
        primary_source_name=primary.source_name if primary else None,
        primary_source_url=primary.url if primary else None,
    )


@router.get("/", response_model=SectionedFeed)
def get_sectioned_feed(db: Session = Depends(get_db)):
    """
    Returns the full homepage feed, organized into sections.
    Events are ranked and sectioned based on user preferences.
    """
    prefs = _get_preferences(db)

    # Load all events — most recently updated first
    events = (
        db.query(Event)
        .filter(Event.title.isnot(None))  # only events that have been AI-analyzed
        .order_by(Event.last_updated_at.desc())
        .limit(500)  # cap to keep it fast
        .all()
    )

    sectioned = section_events(events, prefs)

    # Build the response, converting each (event, reason) pair to EventCard
    return SectionedFeed(
        critical=[_event_to_card(e, r) for e, r in sectioned["critical"]],
        local=[_event_to_card(e, r) for e, r in sectioned["local"]],
        national=[_event_to_card(e, r) for e, r in sectioned["national"]],
        world=[_event_to_card(e, r) for e, r in sectioned["world"]],
        technology=[_event_to_card(e, r) for e, r in sectioned["technology"]],
        business=[_event_to_card(e, r) for e, r in sectioned["business"]],
        science=[_event_to_card(e, r) for e, r in sectioned["science"]],
    )


@router.get("/{event_id}", response_model=EventDetail)
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """
    Returns full event detail including all articles.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    prefs = _get_preferences(db)
    from app.ranking.ranker import _compute_user_interest_score
    _, reason = _compute_user_interest_score(event, prefs)

    card = _event_to_card(event, reason)

    return EventDetail(
        **card.model_dump(),
        articles=[
            ArticleOut.model_validate(a) for a in event.articles
        ],
    )

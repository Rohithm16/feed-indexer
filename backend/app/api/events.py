"""Events API for the homepage and event detail pages."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.models.user_prefs import UserPreferences
from app.ranking.ranker import section_events
from app.schemas.article import ArticleOut
from app.schemas.event import EventCard, EventDetail, SectionedFeed

router = APIRouter(prefix="/api/events", tags=["events"])
logger = logging.getLogger(__name__)


def _get_preferences(db: Session, user: User | None) -> UserPreferences | None:
    if not user:
        return None
    if user.preferences:
        return user.preferences
    prefs = UserPreferences(user_id=user.id, preferred_topics=[], trusted_publishers=[], country="us")
    db.add(prefs)
    db.flush()
    return prefs


def _event_to_card(event: Event, reason: str = "") -> EventCard:
    articles = sorted(
        event.articles or [],
        key=lambda a: (a.published_at or datetime.min.replace(tzinfo=UTC), a.source_tier or 2),
    )
    primary = articles[0] if articles else None
    return EventCard(
        id=event.id,
        title=event.title,
        summary=event.summary,
        why_it_matters=event.why_it_matters,
        category=event.category,
        tags=event.tags or [],
        importance_score=event.importance_score or 0.0,
        is_critical=event.is_critical or False,
        source_count=len(event.articles or []),
        first_seen_at=event.first_seen_at,
        last_updated_at=event.last_updated_at,
        recommendation_reason=reason,
        primary_source_name=primary.source_name if primary else None,
        primary_source_url=primary.url if primary else None,
    )


@router.get("/", response_model=SectionedFeed)
def get_sectioned_feed(db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    prefs = _get_preferences(db, user)
    events = (
        db.query(Event)
        .filter(Event.title.isnot(None))
        .order_by(Event.last_updated_at.desc())
        .limit(500)
        .all()
    )
    sectioned = section_events(events, prefs)
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
def get_event_detail(event_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    prefs = _get_preferences(db, user)
    from app.ranking.ranker import _compute_user_interest_score
    _, reason = _compute_user_interest_score(event, prefs)
    card = _event_to_card(event, reason)
    return EventDetail(**card.model_dump(), articles=[ArticleOut.model_validate(a) for a in event.articles or []])

"""Events API for the homepage and event detail pages."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_optional
from app.constants import DEFAULT_COUNTRIES
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
    prefs = UserPreferences(
        user_id=user.id,
        preferred_topics=[],
        trusted_publishers=[],
        countries=list(DEFAULT_COUNTRIES),
    )
    db.add(prefs)
    db.flush()
    return prefs


def _primary_article(event: Event):
    """Pick the representative article for an event's "Read original" link.

    Best source tier first (tier 1 = most credible), then most recent
    within that tier.
    """
    articles = event.articles or []
    if not articles:
        return None
    return min(
        articles,
        key=lambda a: (
            a.source_tier or 2,
            -(a.published_at.timestamp() if a.published_at else 0),
        ),
    )


def _event_to_card(event: Event, reason: str = "") -> EventCard:
    primary = _primary_article(event)
    return EventCard(
        id=event.id,
        title=event.title,
        summary=event.summary,
        why_it_matters=event.why_it_matters,
        category=event.category,
        country=event.country,
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


def _event_to_detail(event: Event, reason: str = "") -> EventDetail:
    """Builds EventDetail directly, rather than constructing an EventCard
    and re-parsing it through model_dump() just to add the articles field.
    """
    primary = _primary_article(event)
    return EventDetail(
        id=event.id,
        title=event.title,
        summary=event.summary,
        why_it_matters=event.why_it_matters,
        category=event.category,
        country=event.country,
        tags=event.tags or [],
        importance_score=event.importance_score or 0.0,
        is_critical=event.is_critical or False,
        source_count=len(event.articles or []),
        first_seen_at=event.first_seen_at,
        last_updated_at=event.last_updated_at,
        recommendation_reason=reason,
        primary_source_name=primary.source_name if primary else None,
        primary_source_url=primary.url if primary else None,
        articles=[ArticleOut.model_validate(a) for a in event.articles or []],
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
        national={
            country: [_event_to_card(e, r) for e, r in pairs]
            for country, pairs in sectioned["national"].items()
        },
        world=[_event_to_card(e, r) for e, r in sectioned["world"]],
        tech_science=[_event_to_card(e, r) for e, r in sectioned["tech_science"]],
        business_finance=[_event_to_card(e, r) for e, r in sectioned["business_finance"]],
    )


@router.get("/{event_id}", response_model=EventDetail)
def get_event_detail(event_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    prefs = _get_preferences(db, user)
    from app.ranking.ranker import _compute_user_interest_score
    _, reason = _compute_user_interest_score(event, prefs)
    return _event_to_detail(event, reason)
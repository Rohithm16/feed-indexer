"""Event model.

An Event is the aggregation unit: multiple articles from independent
publishers can describe the same underlying news event.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.time import utcnow_naive


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # Gemini-generated language fields, with local fallbacks when Gemini is down.
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    tags = Column(JSON, default=list)

    # Local classification and scoring. Gemini must not own these decisions.
    category = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=True)
    scope = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    importance_score = Column(Float, default=0.0, index=True)
    source_quality_score = Column(Float, default=0.0)
    publisher_count = Column(Integer, default=0)
    is_critical = Column(Boolean, default=False)
    scoring_debug = Column(JSON, default=dict)

    # Gemini call minimization.
    summary_generated_at = Column(DateTime, nullable=True)
    summary_version = Column(Integer, default=1)
    last_summarized_event_state = Column(String(128), nullable=True)

    first_seen_at = Column(DateTime, default=utcnow_naive, index=True)
    last_updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive, index=True)

    articles = relationship(
        "Article",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="joined",
    )

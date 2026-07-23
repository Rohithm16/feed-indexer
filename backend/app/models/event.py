"""
Event model — the primary entity in the database.
An event represents a news story, with one or more articles reporting on it.
All AI-generated content lives here.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # AI-generated content (filled in by Gemini after clustering)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)       # e.g. "technology", "world"
    tags = Column(JSON, default=list)                   # ["AI", "regulation", ...]

    # Scoring
    importance_score = Column(Float, default=0.0)       # 0–100, objective
    user_interest_score = Column(Float, default=0.0)    # computed at query time

    # Critical flag — always shown at top regardless of user preferences
    is_critical = Column(Boolean, default=False)

    # Country/region for local/national sections
    country = Column(String(50), nullable=True)

    # Timestamps
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # All articles that report on this event
    articles = relationship("Article", back_populates="event", lazy="joined")

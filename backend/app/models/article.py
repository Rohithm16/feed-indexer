"""
Article model — represents a single piece of content from an RSS feed.
Each article belongs to an Event (after deduplication/clustering).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)

    # The event this article was clustered into (set after deduplication)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)

    # Core content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)

    # Where it came from
    source_name = Column(String(200), nullable=False)   # e.g. "BBC World Service"
    source_url = Column(String(500), nullable=True)     # feed URL
    category = Column(String(100), nullable=True)       # e.g. "technology"
    country = Column(String(50), nullable=True)         # e.g. "uk", "us", "world"

    created_at = Column(DateTime, default=datetime.utcnow)

    # Back-reference to the parent event
    event = relationship("Event", back_populates="articles")

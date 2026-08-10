"""Article model.

An Article is one publisher's RSS entry. Articles are preserved even when only
a representative subset is sent to Gemini.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.time import utcnow_naive


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # url is the original external link. normalized_url is used for uniqueness.
    url = Column(String(1000), unique=True, nullable=False, index=True)
    normalized_url = Column(String(1000), unique=True, nullable=True, index=True)
    published_at = Column(DateTime, nullable=True, index=True)

    source_name = Column(String(200), nullable=False)
    source_url = Column(String(500), nullable=True)
    publisher_domain = Column(String(255), nullable=True)
    source_tier = Column(Integer, default=2)
    category = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    language = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=utcnow_naive)

    event = relationship("Event", back_populates="articles")

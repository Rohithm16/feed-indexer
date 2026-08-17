"""Per-user preference model."""

from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)

    preferred_topics = Column(JSON, default=list)
    trusted_publishers = Column(JSON, default=list)
    # Legacy single-value columns, unused going forward -- kept rather
    # than doing a destructive migration. `countries` replaces `country`;
    # `city` was retired when local/city-based news was removed.
    country = Column(String(100), default="us")
    city = Column(String(100), nullable=True)
    countries = Column(JSON, default=lambda: ["in"])

    user = relationship("User", back_populates="preferences")
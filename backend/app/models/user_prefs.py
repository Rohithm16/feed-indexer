"""
UserPreferences model — stores a single user's topic and publisher preferences.
For the MVP there's just one preference row (single-user mode).
"""

from sqlalchemy import Column, Integer, String, JSON

from app.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    # Topics the user cares about — e.g. ["technology", "science", "business"]
    preferred_topics = Column(JSON, default=list)

    # Publisher names the user trusts — e.g. ["BBC", "Reuters"]
    trusted_publishers = Column(JSON, default=list)

    # Location for local/national news
    country = Column(String(100), default="us")
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

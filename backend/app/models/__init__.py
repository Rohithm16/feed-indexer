"""Model exports for SQLAlchemy relationship resolution."""

from app.models.article import Article
from app.models.event import Event
from app.models.user import User
from app.models.user_prefs import UserPreferences

__all__ = ["Article", "Event", "User", "UserPreferences"]

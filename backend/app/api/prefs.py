"""
Preferences API — get and update user preferences.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_prefs import UserPreferences
from app.schemas.user_prefs import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _get_or_create_prefs(db: Session) -> UserPreferences:
    """Get existing preferences or create a default row."""
    prefs = db.query(UserPreferences).first()
    if not prefs:
        prefs = UserPreferences(
            preferred_topics=[],
            trusted_publishers=[],
            country="us",
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db)):
    """Returns current user preferences."""
    return _get_or_create_prefs(db)


@router.put("/", response_model=PreferencesOut)
def update_preferences(data: PreferencesIn, db: Session = Depends(get_db)):
    """
    Update user preferences. Replaces all fields — send the full object.
    """
    prefs = _get_or_create_prefs(db)
    prefs.preferred_topics = data.preferred_topics
    prefs.trusted_publishers = data.trusted_publishers
    prefs.country = data.country
    prefs.state = data.state
    prefs.city = data.city
    db.commit()
    db.refresh(prefs)
    return prefs

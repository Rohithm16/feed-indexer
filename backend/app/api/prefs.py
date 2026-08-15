"""User-scoped preferences API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_prefs import UserPreferences
from app.schemas.user_prefs import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _get_or_create_prefs(db: Session, user: User) -> UserPreferences:
    if user.preferences:
        return user.preferences
    prefs = UserPreferences(user_id=user.id, preferred_topics=[], trusted_publishers=[], country="us", city=None)
    db.add(prefs)
    db.flush()
    return prefs


@router.get("/", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_or_create_prefs(db, user)


@router.put("/", response_model=PreferencesOut)
def update_preferences(data: PreferencesIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prefs = _get_or_create_prefs(db, user)
    prefs.preferred_topics = data.preferred_topics
    prefs.trusted_publishers = data.trusted_publishers
    prefs.country = data.country
    prefs.city = data.city
    db.commit()
    db.refresh(prefs)
    return prefs

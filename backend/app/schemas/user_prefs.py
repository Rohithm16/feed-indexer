"""
Pydantic schemas for user preferences.
"""

from typing import List, Optional
from pydantic import BaseModel


class PreferencesIn(BaseModel):
    """Request body when updating preferences."""
    preferred_topics: List[str] = []
    trusted_publishers: List[str] = []
    country: str = "us"
    state: Optional[str] = None
    city: Optional[str] = None


class PreferencesOut(PreferencesIn):
    """Response when fetching preferences."""
    id: int

    model_config = {"from_attributes": True}

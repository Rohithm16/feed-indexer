"""Pydantic schemas for per-user preferences."""

from typing import Optional

from pydantic import BaseModel


class PreferencesIn(BaseModel):
    preferred_topics: list[str] = []
    trusted_publishers: list[str] = []
    country: str = "us"
    state: Optional[str] = None
    city: Optional[str] = None


class PreferencesOut(PreferencesIn):
    id: int
    user_id: int

    model_config = {"from_attributes": True}

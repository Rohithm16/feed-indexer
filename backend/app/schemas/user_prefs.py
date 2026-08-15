"""Pydantic schemas for per-user preferences."""

from pydantic import BaseModel


class PreferencesIn(BaseModel):
    preferred_topics: list[str] = []
    trusted_publishers: list[str] = []
    country: str = "us"
    city: str | None = None


class PreferencesOut(PreferencesIn):
    id: int
    user_id: int

    model_config = {"from_attributes": True}

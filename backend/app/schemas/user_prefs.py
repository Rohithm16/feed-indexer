"""Pydantic schemas for per-user preferences."""

from pydantic import BaseModel, field_validator

from app.constants import DEFAULT_COUNTRIES, SUPPORTED_COUNTRIES


class PreferencesIn(BaseModel):
    preferred_topics: list[str] = []
    trusted_publishers: list[str] = []
    countries: list[str] = list(DEFAULT_COUNTRIES)

    @field_validator("countries")
    @classmethod
    def _validate_countries(cls, value: list[str]) -> list[str]:
        valid = [c for c in value if c in SUPPORTED_COUNTRIES]
        return valid or list(DEFAULT_COUNTRIES)


class PreferencesOut(PreferencesIn):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
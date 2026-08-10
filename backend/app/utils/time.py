"""UTC datetime helpers used across ingestion and ranking."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return an aware UTC datetime."""
    return datetime.now(UTC)


def utcnow_naive() -> datetime:
    """Return a naive UTC datetime for the existing SQLAlchemy DateTime fields."""
    return utcnow().replace(tzinfo=None)


def to_utc_naive(value: datetime | None) -> datetime | None:
    """Normalize aware or naive datetimes to naive UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)

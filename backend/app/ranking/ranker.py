""" Ranker — scores and sorts events for the homepage feed. """
from typing import Optional
from app.models.event import Event
from app.models.user_prefs import UserPreferences


def _compute_user_interest_score(
    event: Event, prefs: Optional[UserPreferences],
) -> tuple[float, str]:
    """Returns (bonus_score, reason_string)."""
    if not prefs:
        return 0.0, "High importance"

    bonus = 0.0
    reasons = []

    # Category match
    if event.category and event.category in (prefs.preferred_topics or []):
        bonus += 20
        reasons.append(f"Matches your interest in {event.category}")

    # Trusted publisher
    article_sources = {a.source_name for a in (event.articles or [])}
    trusted = set(prefs.trusted_publishers or [])
    matching_sources = article_sources & trusted
    if matching_sources:
        bonus += 10
        reasons.append(f"Trusted source: {', '.join(matching_sources)}")

    # Country match (fixed: only if both are non‑null and equal)
    if prefs.country and event.country and event.country == prefs.country:
        bonus += 15
        reasons.append("Local to your region")

    if not reasons:
        importance = event.importance_score or 0
        if importance >= 70:
            reasons.append("High global importance")
        elif importance >= 40:
            reasons.append("Significant story")
        else:
            reasons.append("Recent development")

    return bonus, " · ".join(reasons)


def rank_events(
    events: list[Event],
    prefs: Optional[UserPreferences] = None,
) -> list[tuple[Event, str]]:
    """Score and sort events. Critical events are excluded here."""
    scored = []
    for event in events:
        if event.is_critical:
            continue
        user_bonus, reason = _compute_user_interest_score(event, prefs)
        final_score = (event.importance_score or 0) + user_bonus
        scored.append((final_score, reason, event))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(event, reason) for _, reason, event in scored]


def section_events(
    events: list[Event],
    prefs: Optional[UserPreferences] = None,
) -> dict:
    """
    Divide events into sections.
    - Minor news (importance_score ≤ 0) are filtered out unless show_minor_news is True.
    - Local section only shows events whose country matches the user's country.
    """
    sections: dict[str, list] = {
        "critical": [],
        "local": [],
        "national": [],
        "world": [],
        "technology": [],
        "business": [],
        "science": [],
    }

    user_country = prefs.country if prefs else None
    # show_minor = prefs.show_minor_news if prefs else False

    for event in events:
        # ---- Filter minor news ----
        if (event.importance_score or 0) <= 0: 
        # and not show_minor:
            continue

        # ---- Critical ----
        if event.is_critical:
            _, reason = _compute_user_interest_score(event, prefs)
            sections["critical"].append((event, "Critical event"))
            continue

        _, reason = _compute_user_interest_score(event, prefs)
        category = (event.category or "world").lower()

        # ---- Local: only if country matches exactly ----
        if (
            user_country
            and event.country
            and event.country == user_country
            and category in ("national", "politics")
        ):
            sections["local"].append((event, reason))

        # ---- National ----
        elif category == "national":
            sections["national"].append((event, reason))

        # ---- World ----
        elif category in ("world", "politics"):
            sections["world"].append((event, reason))

        # ---- Technology ----
        elif category == "technology":
            sections["technology"].append((event, reason))

        # ---- Business ----
        elif category in ("business", "finance"):
            sections["business"].append((event, reason))

        # ---- Science ----
        elif category in ("science", "health"):
            sections["science"].append((event, reason))

        # ---- Fallback ----
        else:
            sections["world"].append((event, reason))

    # Sort each section by importance
    for key in sections:
        sections[key].sort(
            key=lambda pair: pair[0].importance_score or 0,
            reverse=True,
        )

    return sections
"""
Ranker — scores and sorts events for the homepage feed.

Ranking formula:
  final_score = importance_score + user_interest_bonus

User interest bonus:
  +20 if event category matches a preferred topic
  +10 if any article is from a trusted publisher
  +15 if event is in the user's country

Critical events bypass ranking and always appear in the critical section.

Each event also gets a human-readable `recommendation_reason` string
so the UI can show transparency about why it's shown.
"""

from typing import Optional
from app.models.event import Event
from app.models.user_prefs import UserPreferences


def _compute_user_interest_score(
    event: Event,
    prefs: Optional[UserPreferences],
) -> tuple[float, str]:
    """
    Returns (bonus_score, reason_string).
    reason_string is a human-readable explanation for the UI.
    """
    if not prefs:
        return 0.0, "High importance"

    bonus = 0.0
    reasons = []

    # Category matches preferred topic
    if event.category and event.category in (prefs.preferred_topics or []):
        bonus += 20
        reasons.append(f"Matches your interest in {event.category}")

    # An article comes from a trusted publisher
    article_sources = {a.source_name for a in (event.articles or [])}
    trusted = set(prefs.trusted_publishers or [])
    matching_sources = article_sources & trusted
    if matching_sources:
        bonus += 10
        reasons.append(f"Trusted source: {', '.join(matching_sources)}")

    # Local relevance
    if prefs.country and event.country == prefs.country:
        bonus += 15
        reasons.append("Local to your region")

    # Default reason if nothing personalized
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
    """
    Score and sort events for display.

    Returns a list of (event, recommendation_reason) tuples,
    sorted by final score descending.
    Critical events are excluded here — they're handled separately.
    """
    scored = []
    for event in events:
        if event.is_critical:
            continue  # critical events are pinned separately

        user_bonus, reason = _compute_user_interest_score(event, prefs)
        final_score = (event.importance_score or 0) + user_bonus
        scored.append((final_score, reason, event))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(event, reason) for _, reason, event in scored]


def section_events(
    events: list[Event],
    prefs: Optional[UserPreferences] = None,
) -> dict:
    """
    Divide events into the homepage sections:
    critical, local, national, world, technology, business, science.

    Returns a dict mapping section name → list of (event, reason) tuples.
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

    for event in events:
        reason: str

        if event.is_critical:
            _, reason = _compute_user_interest_score(event, prefs)
            sections["critical"].append((event, "Critical event"))
            continue

        _, reason = _compute_user_interest_score(event, prefs)
        category = (event.category or "world").lower()

        # Local/national placement based on country match
        if user_country and event.country == user_country and category in ("national", "politics"):
            sections["local"].append((event, reason))
        elif category == "national":
            sections["national"].append((event, reason))
        elif category in ("world", "politics"):
            sections["world"].append((event, reason))
        elif category == "technology":
            sections["technology"].append((event, reason))
        elif category in ("business", "finance"):
            sections["business"].append((event, reason))
        elif category in ("science", "health"):
            sections["science"].append((event, reason))
        else:
            sections["world"].append((event, reason))

    # Sort each section by importance score
    for key in sections:
        sections[key].sort(
            key=lambda pair: pair[0].importance_score or 0,
            reverse=True,
        )

    return sections

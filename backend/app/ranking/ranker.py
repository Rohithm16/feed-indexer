"""Ranker — scores and sorts events for the homepage feed."""
from app.models.event import Event
from app.models.user_prefs import UserPreferences


def _compute_user_interest_score(event: Event, prefs: UserPreferences | None) -> tuple[float, str]:
    """Return a personalization bonus and a human-readable explanation."""
    if not prefs:
        return 0.0, "High importance"

    bonus = 0.0
    reasons: list[str] = []

    if event.category and event.category in (prefs.preferred_topics or []):
        bonus += 18.0
        reasons.append(f"Matches your interest in {event.category}")

    article_sources = {a.source_name for a in (event.articles or [])}
    trusted = set(prefs.trusted_publishers or [])
    matching_sources = article_sources & trusted
    if matching_sources:
        bonus += 12.0
        reasons.append(f"Trusted source: {', '.join(sorted(matching_sources))}")

    if prefs.city and event.country and event.country == prefs.country:
        event_title = (event.title or "").lower()
        city_name = prefs.city.lower()
        if city_name in event_title:
            bonus += 22.0
            reasons.append(f"Local to {prefs.city}")
        elif event.category in {"national", "politics"}:
            bonus += 8.0
            reasons.append("Relevant to your country")

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
    prefs: UserPreferences | None = None,
) -> list[tuple[Event, str]]:
    """Score and sort events by objective importance plus personalization."""
    scored: list[tuple[float, str, Event]] = []
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
    prefs: UserPreferences | None = None,
) -> dict:
    """
    Divide events into sections.
    - Minor news with negligible importance is filtered out.
    - Local section prioritizes city-level matches when a city is configured.
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
    user_city = (prefs.city or "").strip().lower() if prefs else ""

    for event in events:
        if (event.importance_score or 0) <= 0:
            continue

        # ---- Critical ----
        if event.is_critical:
            _, reason = _compute_user_interest_score(event, prefs)
            sections["critical"].append((event, "Critical event"))
            continue

        _, reason = _compute_user_interest_score(event, prefs)
        category = (event.category or "world").lower()

        is_city_match = bool(user_city and user_city in (event.title or "").lower())
        is_same_country = bool(user_country and event.country and event.country == user_country)
        is_local_match = is_same_country and is_city_match

        if is_local_match:
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
    for key, section in sections.items():
        section.sort(
            key=lambda pair: ((pair[0].importance_score or 0) + _compute_user_interest_score(pair[0], prefs)[0]),
            reverse=True,
        )

    return sections
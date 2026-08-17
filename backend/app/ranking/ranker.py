"""Ranker — scores and sorts events for the homepage feed."""
from app.constants import DEFAULT_COUNTRIES, SUPPORTED_COUNTRIES
from app.models.event import Event
from app.models.user_prefs import UserPreferences

# Content-type routing for non-national events. Uses the scorer's
# content-derived event_type, NOT event.category (which is just a static
# tag copied from whichever RSS feed the article came from -- see the
# "event.category bug" discussion). Tech and science are merged into one
# section; finance/economy/corporate merge into business_finance; every
# other event_type (disaster, conflict, election, health, law, diplomacy,
# entertainment, sports, lifestyle, etc.) falls into world, which is the
# intentional catch-all for everything that isn't specifically
# tech/science, business/finance, or a national story.
_TECH_SCIENCE_TYPES = {"technology", "science"}
_BUSINESS_FINANCE_TYPES = {"finance", "economy", "corporate"}

# Caps exist for three reasons: keeps the feed to genuinely important
# stories instead of a long tail of 25-and-under noise, skips Gemini
# calls for events that would just get evicted anyway, and keeps the DB
# from accumulating events indefinitely. National is a per-country cap
# (each selected country gets its own 6, not 6 shared across both).
SECTION_CAPS = {
    "national": 6,
    "world": 10,
    "tech_science": 6,
    "business_finance": 6,
}


def classify_event_bucket(event: Event) -> str:
    """Which section an event belongs to, independent of any particular
    user's country selection -- "national:<code>" for any of the globally
    supported countries, otherwise content-type routing. Used both by
    section_events() below (per-request, filtered to a user's selected
    countries) and by cleanup.enforce_section_caps (global storage-level
    eviction, independent of any one user).
    """
    if event.country in SUPPORTED_COUNTRIES:
        return f"national:{event.country}"
    event_type = (event.event_type or "").lower()
    if event_type in _TECH_SCIENCE_TYPES:
        return "tech_science"
    if event_type in _BUSINESS_FINANCE_TYPES:
        return "business_finance"
    return "world"


def _selected_countries(prefs: UserPreferences | None) -> list[str]:
    if prefs:
        countries = [c for c in (getattr(prefs, "countries", None) or []) if c in SUPPORTED_COUNTRIES]
        if countries:
            return countries
    return DEFAULT_COUNTRIES


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

    if event.country and event.country in _selected_countries(prefs):
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
        user_bonus, reason = _compute_user_interest_score(event, prefs)
        if event.is_critical:
            reason = "Critical event" if not reason else reason
        final_score = (event.importance_score or 0) + user_bonus
        scored.append((final_score, reason, event))

    scored.sort(key=lambda x: (x[2].is_critical, x[0]), reverse=True)
    return [(event, reason) for _, reason, event in scored]


def section_events(
    events: list[Event],
    prefs: UserPreferences | None = None,
) -> dict:
    """
    Divide events into sections and apply per-section importance caps.

    National takes priority over content-based routing: a technology
    story out of a selected country lands in that country's National
    sub-feed, not Tech & Science, even though its content type is
    "technology". Only events NOT matching a selected country fall
    through to content-based routing (tech_science / business_finance /
    world catch-all).
    """
    selected_countries = _selected_countries(prefs)
    sections: dict = {
        "critical": [],
        "national": {country: [] for country in selected_countries},
        "world": [],
        "tech_science": [],
        "business_finance": [],
    }

    for event in events:
        if (event.importance_score or 0) <= 0:
            continue

        _, reason = _compute_user_interest_score(event, prefs)

        if event.is_critical:
            sections["critical"].append((event, "Critical event"))
            continue

        if event.country in selected_countries:
            sections["national"][event.country].append((event, reason))
            continue

        # Content-type routing for everything else, including events tied
        # to a supported country the user just didn't select (e.g. an
        # India tech story for a US-only user) -- falls through to
        # Tech & Science / Business & Finance / World rather than
        # disappearing entirely.
        event_type = (event.event_type or "").lower()
        if event_type in _TECH_SCIENCE_TYPES:
            sections["tech_science"].append((event, reason))
        elif event_type in _BUSINESS_FINANCE_TYPES:
            sections["business_finance"].append((event, reason))
        else:
            sections["world"].append((event, reason))

    def _sorted_capped(pairs: list, cap: int) -> list:
        pairs.sort(key=lambda pair: (pair[0].importance_score or 0), reverse=True)
        return pairs[:cap]

    sections["critical"].sort(key=lambda pair: (pair[0].importance_score or 0), reverse=True)
    for country in list(sections["national"].keys()):
        sections["national"][country] = _sorted_capped(sections["national"][country], SECTION_CAPS["national"])
    sections["world"] = _sorted_capped(sections["world"], SECTION_CAPS["world"])
    sections["tech_science"] = _sorted_capped(sections["tech_science"], SECTION_CAPS["tech_science"])
    sections["business_finance"] = _sorted_capped(sections["business_finance"], SECTION_CAPS["business_finance"])

    return sections
"""Local hybrid event scoring for objective importance."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.models.article import Article
from app.models.event import Event
from app.utils.time import utcnow_naive


LOW_VALUE_TERMS = {
    "celebrity",
    "gossip",
    "lifestyle",
    "wellness",
    "listicle",
    "recipe",
    "travel",
    "fashion",
    "opinion",
    "commentary",
    "promo",
    "promotion",
    "ad",
    "trivial",
    "routine",
}

HIGH_IMPACT_TERMS = {
    "war",
    "strike",
    "attack",
    "bomb",
    "killed",
    "death",
    "deaths",
    "injury",
    "injured",
    "election",
    "vote",
    "policy",
    "budget",
    "rate",
    "inflation",
    "crisis",
    "court",
    "law",
    "disaster",
    "flood",
    "earthquake",
    "wildfire",
    "earthquake",
    "pandemic",
    "outbreak",
    "bank",
    "market",
    "stock",
    "supply",
    "infrastructure",
    "airport",
    "bridge",
    "power",
    "energy",
    "virus",
    "ai",
    "chip",
    "launch",
    "space",
    "satellite",
    "nuclear",
    "security",
}

EVENT_TYPE_KEYWORDS = {
    "conflict": ["war", "strike", "attack", "military", "troops", "conflict"],
    "disaster": ["flood", "earthquake", "wildfire", "storm", "cyclone", "disaster"],
    "terrorism": ["terror", "bomb", "shooting", "attack"],
    "election": ["election", "vote", "poll", "campaign"],
    "government_policy": ["policy", "bill", "budget", "law", "government", "ministry"],
    "economy": ["inflation", "growth", "economy", "gdp", "trade"],
    "finance": ["bank", "market", "stock", "rate", "bond", "currency"],
    "corporate": ["company", "firm", "merger", "acquisition", "earnings"],
    "science": ["scientists", "study", "research", "space", "satellite", "rocket"],
    "technology": ["ai", "chip", "tech", "software", "launch", "startup"],
    "health": ["health", "virus", "pandemic", "hospital", "vaccine"],
    "law": ["court", "judge", "lawsuit", "legal", "supreme"],
    "diplomacy": ["summit", "diplomatic", "foreign", "treaty", "sanction"],
    "infrastructure": ["bridge", "airport", "rail", "power", "grid", "infrastructure"],
    "sports": ["sport", "match", "tournament", "cup", "league"],
    "entertainment": ["film", "movie", "music", "album", "awards"],
    "lifestyle": ["lifestyle", "fashion", "travel", "recipe", "wellness"],
}

SCOPE_HINTS = {
    "global": ["global", "worldwide", "international"],
    "national": ["national", "india", "us", "uk", "country"],
    "regional": ["state", "regional", "province", "district", "city"],
    "local": ["local", "city", "town", "district", "metro"],
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def _extract_numbers(text: str) -> list[int]:
    return [int(token) for token in re.findall(r"\b\d+\b", text)]


def _get_event_type(text: str) -> str:
    lowered = _normalize_text(text)
    match_scores: list[tuple[str, int]] = []
    for event_type, keywords in EVENT_TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score:
            match_scores.append((event_type, score))
    if not match_scores:
        return "local"
    match_scores.sort(key=lambda item: item[1], reverse=True)
    return match_scores[0][0]


def _get_scope(text: str) -> str:
    lowered = _normalize_text(text)
    for scope, hints in SCOPE_HINTS.items():
        if any(hint in lowered for hint in hints):
            return scope
    return "national"


def _source_quality_score(articles: list[Article]) -> float:
    if not articles:
        return 0.0
    tier_score = 0.0
    for article in articles:
        tier = article.source_tier or 2
        tier_score += 90 - min(40, (tier - 1) * 15)
    average_tier = tier_score / len(articles)
    return round(min(100.0, average_tier), 2)


def _evidence_score(articles: list[Article]) -> float:
    if not articles:
        return 0.0
    unique_publishers = len({article.source_name for article in articles if article.source_name})
    if unique_publishers <= 1:
        return 25.0 + min(15.0, unique_publishers * 5.0)
    if unique_publishers == 2:
        return 45.0
    if unique_publishers == 3:
        return 60.0
    if unique_publishers == 4:
        return 70.0
    return 78.0 - min(10.0, (unique_publishers - 5) * 0.8)


def _novelty_score(event: Event, articles: list[Article]) -> float:
    if not articles:
        return 40.0
    latest = max((a.published_at or utcnow_naive() for a in articles), default=utcnow_naive())
    if isinstance(latest, datetime):
        now = datetime.now(tz=timezone.utc)
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        age = max(0.0, (now - latest).total_seconds() / 3600)
        freshness = max(0.0, 100.0 - min(80.0, age * 1.6))
    else:
        freshness = 60.0
    title_length_penalty = max(0.0, 8.0 - min(8.0, len(event.title or "") / 25.0))
    return round(min(100.0, freshness - title_length_penalty + 10.0), 2)


def _low_value_penalty(text: str) -> float:
    lowered = _normalize_text(text)
    if not lowered:
        return 0.0
    matches = sum(1 for term in LOW_VALUE_TERMS if term in lowered)
    if matches:
        return min(22.0, 6.0 + matches * 3.0)
    if "opinion" in lowered or "analysis" in lowered:
        return 8.0
    return 0.0


def score_event(event: Event, articles: list[Article] | None = None) -> tuple[float, dict[str, Any]]:
    """Score an event at the event level using local deterministic signals."""
    article_list = articles or list(event.articles or [])
    if not article_list:
        return 0.0, {"reasons": ["No articles available"]}

    combined_text = " ".join(
        filter(None, [article.title, article.description or "", event.title or "", event.summary or ""])
    )
    lowered = _normalize_text(combined_text)
    numbers = _extract_numbers(combined_text)

    content_score = 35.0
    for term in HIGH_IMPACT_TERMS:
        if term in lowered:
            content_score += 2.5
    if numbers:
        content_score += min(14.0, len(numbers) * 1.8)
    if re.search(r"\b(major|massive|deadly|devastating|breaking|escalat|substantial)\b", lowered):
        content_score += 9.0

    impact_score = 28.0
    if re.search(r"\b(court|law|policy|budget|rate|inflation|crisis|strike|war|attack|disaster|pandemic)\b", lowered):
        impact_score += 24.0
    if re.search(r"\b(death|deaths|injury|injured|killed|fatal|affected|evacuat)\b", lowered):
        impact_score += 16.0
    if re.search(r"\b(market|stock|bank|currency|trade|supply|power|grid|infrastructure)\b", lowered):
        impact_score += 12.0

    scope_label = _get_scope(lowered)
    scope_score = {"global": 90.0, "national": 78.0, "regional": 66.0, "local": 54.0}.get(scope_label, 60.0)

    evidence_score = _evidence_score(article_list)
    source_quality = _source_quality_score(article_list)
    novelty_score = _novelty_score(event, article_list)
    low_value_penalty = _low_value_penalty(lowered)

    event_type = _get_event_type(lowered)
    type_boost = {
        "conflict": 16.0,
        "terrorism": 14.0,
        "disaster": 14.0,
        "election": 12.0,
        "government_policy": 10.0,
        "economy": 9.0,
        "finance": 8.0,
        "health": 8.0,
        "law": 8.0,
        "diplomacy": 7.0,
        "science": 7.0,
        "technology": 7.0,
        "infrastructure": 7.0,
        "corporate": 4.0,
        "sports": 1.0,
        "entertainment": 0.0,
        "lifestyle": -6.0,
        "local": 0.0,
    }.get(event_type, 0.0)

    final_score = (
        0.28 * content_score
        + 0.22 * impact_score
        + 0.15 * scope_score
        + 0.12 * evidence_score
        + 0.10 * source_quality
        + 0.08 * novelty_score
        + 0.05 * type_boost
        - 0.10 * low_value_penalty
    )

    final_score = max(0.0, min(100.0, round(final_score, 2)))

    debug = {
        "event_type": event_type,
        "scope": scope_label,
        "content": round(content_score, 2),
        "impact": round(impact_score, 2),
        "scope_score": round(scope_score, 2),
        "evidence": round(evidence_score, 2),
        "novelty": round(novelty_score, 2),
        "source_quality": round(source_quality, 2),
        "type_boost": round(type_boost, 2),
        "penalty": round(low_value_penalty, 2),
        "publishers": len({article.source_name for article in article_list if article.source_name}),
        "critical": False,
        "reasons": [],
    }

    if event_type in {"conflict", "terrorism", "disaster", "election", "government_policy", "finance", "health", "law"}:
        debug["reasons"].append(f"{event_type.replace('_', ' ')} signal")
    if scope_label in {"global", "national"}:
        debug["reasons"].append(f"{scope_label} scope")
    if evidence_score >= 60:
        debug["reasons"].append("multiple publishers corroborate the story")
    if final_score >= settings.gemini_min_importance_score:
        debug["reasons"].append("high-impact story")
    if low_value_penalty:
        debug["reasons"].append("low-value content penalty")

    return final_score, debug


def apply_scoring_to_event(event: Event, articles: list[Article] | None = None) -> dict[str, Any]:
    score, debug = score_event(event, articles)
    event.importance_score = score
    event.event_type = debug["event_type"]
    event.scope = debug["scope"]
    event.source_quality_score = debug["source_quality"]
    event.publisher_count = debug["publishers"]
    event.scoring_debug = debug
    event.is_critical = score >= 90.0 or any(token in (event.title or "").lower() for token in ["war", "terror", "election", "crisis", "pandemic"])
    return debug

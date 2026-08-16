"""Local hybrid event scoring for objective importance.

Rewrite notes (see chat for full rationale):
- All keyword checks use \\b word-boundary regex instead of naive substring
  `in` checks (the old code matched "us" inside "because", "ad" inside
  "leadership", etc, which silently corrupted scope/low-value detection).
- Impact terms are tiered (strong / moderate / weak). Weak, generic terms
  ("ai", "chip", "launch", "market", "bank", "power") only get meaningful
  weight when they co-occur with a strong/moderate signal or a magnitude
  figure (casualty counts, dollar/percent scale) -- otherwise routine tech
  and business news floods the top of the feed.
- Evidence (publisher corroboration) is now a *multiplicative gate* on the
  final score rather than a ~12% additive term, so single-source stories
  (which dominated the noisy examples you showed) get pulled down hard
  unless they come from a top-tier wire source.
- Quote-led headlines ("'I feel like I'm at war': ...") are a journalism
  convention for opinion/feature pieces; they get an explicit penalty
  instead of being scored as literal hard news.
- Listicle / product-announcement / review content ("Top 5 tips for...",
  "Everything announced at D23", "Review: ...") is detected directly and
  hard-capped, regardless of what keywords happen to appear in it.
- Score floors are much lower so events without real signal actually sink,
  instead of being compressed into a narrow 45-55 band.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.models.article import Article
from app.models.event import Event
from app.utils.time import utcnow_naive


# --------------------------------------------------------------------------
# Term sets & compiled patterns
# --------------------------------------------------------------------------

def _wb_pattern(terms: set[str]) -> re.Pattern:
    """Compile a single alternation pattern with word boundaries around each term."""
    escaped = sorted((re.escape(t) for t in terms), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b")


LOW_VALUE_TERMS = {
    "celebrity", "gossip", "lifestyle", "wellness", "recipe", "travel",
    "fashion", "opinion", "commentary", "promo", "promotion",
    "advertisement", "sponsored", "trivial", "routine", "horoscope",
}
_LOW_VALUE_RE = _wb_pattern(LOW_VALUE_TERMS)

# Strong: rarely a false positive, almost always literal hard news.
STRONG_IMPACT_TERMS = {
    "war", "bombing", "bomb", "killed", "death", "deaths", "earthquake",
    "wildfire", "pandemic", "outbreak", "nuclear", "election", "inflation",
    "tsunami", "coup", "invasion", "massacre", "famine", "genocide",
    "hurricane", "cyclone", "recession",
}
_STRONG_RE = _wb_pattern(STRONG_IMPACT_TERMS)

# Moderate: usually meaningful but noisier than strong terms.
MODERATE_IMPACT_TERMS = {
    "strike", "attack", "injury", "injured", "vote", "policy", "budget",
    "rate", "court", "law", "disaster", "flood", "virus", "security",
    "sanctions", "shutdown", "layoffs", "ceasefire", "evacuation", "crisis",
}
_MODERATE_RE = _wb_pattern(MODERATE_IMPACT_TERMS)

# Weak: extremely generic, only count meaningfully if corroborated by a
# strong/moderate term or a magnitude figure (see below).
WEAK_IMPACT_TERMS = {
    "ai", "chip", "launch", "space", "satellite", "bank", "market",
    "stock", "supply", "infrastructure", "airport", "bridge", "power",
    "energy",
}
_WEAK_RE = _wb_pattern(WEAK_IMPACT_TERMS)

# Numeric magnitude: casualty counts, scale figures. These are much
# stronger evidence of real-world impact than a bare keyword hit.
_MAGNITUDE_RE = re.compile(
    r"\b\d[\d,]*\s*(?:killed|dead|deaths?|injured|displaced|affected|"
    r"evacuated|hospitalized)\b|\b(?:million|billion)\b",
    re.IGNORECASE,
)

_SEVERITY_ADJ_RE = re.compile(
    r"\b(?:major|massive|deadly|devastating|breaking|escalat\w*|substantial)\b",
    re.IGNORECASE,
)

# Content-type detectors: these override keyword-based scoring because they
# reliably signal low editorial weight regardless of topic.
_LISTICLE_RE = re.compile(
    r"\btop\s+\d+\b|\b\d+\s+(?:tips|ways|things|reasons|hacks|secrets)\b|"
    r"\bbest\s+\d+\b",
    re.IGNORECASE,
)
_ANNOUNCEMENT_RE = re.compile(
    r"\beverything (?:announced|revealed|shown)\b|\bwhat('?s| is) (?:new|coming)\b|"
    r"\bhere'?s what\b|\bteased? at\b",
    re.IGNORECASE,
)
_REVIEW_RE = re.compile(
    r"\breview:|hands-on|first look|unboxing|buyer'?s guide", re.IGNORECASE,
)

# A headline opening with a quotation mark is almost always a feature or
# opinion piece built around a quote, not a literal hard-news report.
_QUOTE_LEAD_RE = re.compile(r"^\s*[\"'\u2018\u201c]")

EVENT_TYPE_KEYWORDS = {
    "conflict": {"war", "strike", "attack", "military", "troops", "conflict", "invasion"},
    "disaster": {"flood", "earthquake", "wildfire", "storm", "cyclone", "disaster", "hurricane"},
    "terrorism": {"terror", "bomb", "shooting", "bombing"},
    "election": {"election", "vote", "poll", "campaign", "midterm", "ballot"},
    "government_policy": {"policy", "bill", "budget", "law", "government", "ministry", "regulation"},
    "economy": {"inflation", "growth", "economy", "gdp", "trade", "recession"},
    "finance": {"bank", "market", "stock", "rate", "bond", "currency"},
    "corporate": {"company", "firm", "merger", "acquisition", "earnings", "startup"},
    "science": {"scientists", "study", "research", "space", "satellite", "rocket", "eeg"},
    "technology": {"chip", "tech", "software"},
    "health": {"health", "virus", "pandemic", "hospital", "vaccine"},
    "law": {"court", "judge", "lawsuit", "legal", "supreme"},
    "diplomacy": {"summit", "diplomatic", "foreign", "treaty", "sanctions"},
    "infrastructure": {"bridge", "airport", "rail", "power", "grid", "infrastructure"},
    "sports": {"sport", "match", "tournament", "cup", "league"},
    "entertainment": {"film", "movie", "music", "album", "awards", "season", "trailer",
                       "teaser", "premiere", "d23", "marvel", "starfighter", "ahsoka"},
    "lifestyle": {"lifestyle", "fashion", "travel", "recipe", "wellness"},
}
_EVENT_TYPE_RES = {name: _wb_pattern(kws) for name, kws in EVENT_TYPE_KEYWORDS.items()}

# Tie-break priority when multiple event types score equally (most specific /
# highest-stakes categories win).
_EVENT_TYPE_PRIORITY = [
    "conflict", "terrorism", "disaster", "election", "government_policy",
    "economy", "finance", "health", "law", "diplomacy", "science",
    "infrastructure", "technology", "corporate", "sports", "entertainment",
    "lifestyle",
]

_TYPE_BOOST = {
    "conflict": 16.0, "terrorism": 14.0, "disaster": 14.0, "election": 12.0,
    "government_policy": 10.0, "economy": 9.0, "finance": 8.0, "health": 8.0,
    "law": 8.0, "diplomacy": 7.0, "science": 6.0, "infrastructure": 6.0,
    "technology": 3.0, "corporate": 2.0, "sports": 1.0, "entertainment": -8.0,
    "lifestyle": -8.0, "local": 0.0,
}

SCOPE_HINTS = {
    "local": {"local", "town", "district", "metro"},
    "regional": {"state", "regional", "province"},
    "national": {"national", "india", "us", "usa", "uk", "country", "nationwide"},
    "global": {"global", "worldwide", "international"},
}
_SCOPE_RES = {name: _wb_pattern(hints) for name, hints in SCOPE_HINTS.items()}
# Check most specific first; "global" beats "national" if both present.
_SCOPE_CHECK_ORDER = ["global", "national", "regional", "local"]
_SCOPE_SCORE = {"global": 90.0, "national": 78.0, "regional": 66.0, "local": 54.0}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def _get_event_type(lowered: str) -> str:
    scores = {name: len(pattern.findall(lowered)) for name, pattern in _EVENT_TYPE_RES.items()}
    best = max(scores.values(), default=0)
    if best == 0:
        return "local"
    candidates = [name for name, score in scores.items() if score == best]
    for name in _EVENT_TYPE_PRIORITY:
        if name in candidates:
            return name
    return candidates[0]


def _get_scope(lowered: str) -> str:
    for scope in _SCOPE_CHECK_ORDER:
        if _SCOPE_RES[scope].search(lowered):
            return scope
    return "national"


def _source_quality_score(articles: list[Article]) -> float:
    if not articles:
        return 0.0
    tier_score = 0.0
    for article in articles:
        tier = article.source_tier or 2
        tier_score += 90 - min(40, (tier - 1) * 15)
    return round(min(100.0, tier_score / len(articles)), 2)


def _evidence_multiplier(articles: list[Article]) -> tuple[float, int]:
    """Corroboration acts as a gate on the final score, not a minor additive term.

    A single-source story is capped hard unless it comes from a top-tier
    (tier 1) outlet, in which case it's treated as plausible fast-breaking
    wire coverage rather than penalized as heavily.
    """
    if not articles:
        return 0.0, 0
    unique_publishers = len({a.source_name for a in articles if a.source_name})
    best_tier = min((a.source_tier or 3) for a in articles)

    if unique_publishers <= 1:
        multiplier = 0.72 if best_tier == 1 else 0.5
    elif unique_publishers == 2:
        multiplier = 0.85 if best_tier == 1 else 0.72
    elif unique_publishers == 3:
        multiplier = 0.88
    elif unique_publishers == 4:
        multiplier = 0.95
    else:
        multiplier = 1.0
    return multiplier, unique_publishers


def _novelty_score(event: Event, articles: list[Article]) -> float:
    if not articles:
        return 40.0
    latest = max((a.published_at or utcnow_naive() for a in articles), default=utcnow_naive())
    if isinstance(latest, datetime):
        now = datetime.now(tz=timezone.utc)
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        age_hours = max(0.0, (now - latest).total_seconds() / 3600)
        freshness = max(0.0, 100.0 - min(80.0, age_hours * 1.6))
    else:
        freshness = 60.0
    return round(min(100.0, freshness), 2)


def _low_value_penalty(lowered: str) -> float:
    if not lowered:
        return 0.0
    matches = len(_LOW_VALUE_RE.findall(lowered))
    if matches:
        return min(24.0, 8.0 + matches * 4.0)
    return 0.0


def is_low_editorial_content(title: str, description: str | None = None) -> bool:
    """Shared low-value/listicle/announcement/review detector.

    Used both as an early skip in the ingestion pipeline (avoid spending a
    dedup/embedding call on obvious junk) and implicitly by score_event's
    own content-type gating. Keeping one definition means the pipeline's
    early skip and the scorer's cap can't drift out of sync the way the
    old pipeline._is_low_value keyword list did (it lacked review/listicle
    pattern detection entirely, which is why "Top 5 tips for pregnancy"
    and laptop review pieces were reaching the scorer at all).
    """
    combined = f"{title or ''} {description or ''}"
    if _LISTICLE_RE.search(combined) or _ANNOUNCEMENT_RE.search(combined) or _REVIEW_RE.search(combined):
        return True
    lowered = _normalize_text(combined)
    return bool(_LOW_VALUE_RE.search(lowered))


def score_event(event: Event, articles: list[Article] | None = None) -> tuple[float, dict[str, Any]]:
    """Score an event at the event level using local deterministic signals."""
    article_list = articles or list(event.articles or [])
    if not article_list:
        return 0.0, {"reasons": ["No articles available"]}

    title = event.title or ""
    article_text_parts = [a.title or "" for a in article_list]
    article_text_parts.extend(a.description or "" for a in article_list)
    combined_text = " ".join(filter(None, [*article_text_parts, title, event.summary or ""]))
    lowered = _normalize_text(combined_text)

    # --- content-type gating (listicle / announcement / review) ---
    is_listicle = bool(_LISTICLE_RE.search(combined_text))
    is_announcement = bool(_ANNOUNCEMENT_RE.search(combined_text))
    is_review = bool(_REVIEW_RE.search(combined_text))
    is_low_editorial = is_listicle or is_announcement or is_review

    # --- quote-lead detection (feature/opinion convention) ---
    is_quote_lead = bool(_QUOTE_LEAD_RE.match(title.strip()))

    # --- tiered keyword signal ---
    strong_hits = len(_STRONG_RE.findall(lowered))
    moderate_hits = len(_MODERATE_RE.findall(lowered))
    weak_hits = len(_WEAK_RE.findall(lowered))
    magnitude_hits = len(_MAGNITUDE_RE.findall(lowered))
    has_corroborating_signal = bool(strong_hits or moderate_hits or magnitude_hits)

    content_score = 8.0
    content_score += strong_hits * 9.0
    content_score += moderate_hits * 5.0
    content_score += min(6.0, weak_hits * 2.0) if has_corroborating_signal else min(2.0, weak_hits * 0.5)
    if magnitude_hits:
        content_score += min(16.0, 8.0 + magnitude_hits * 4.0)
    if _SEVERITY_ADJ_RE.search(lowered):
        content_score += 7.0

    impact_score = 6.0
    if strong_hits:
        impact_score += 22.0
    if moderate_hits:
        impact_score += 12.0
    if magnitude_hits:
        impact_score += 14.0

    scope_label = _get_scope(lowered)
    scope_score = _SCOPE_SCORE.get(scope_label, 60.0)

    evidence_multiplier, unique_publishers = _evidence_multiplier(article_list)
    source_quality = _source_quality_score(article_list)
    novelty_score = _novelty_score(event, article_list)
    low_value_penalty = _low_value_penalty(lowered)

    event_type = _get_event_type(lowered)
    type_boost = _TYPE_BOOST.get(event_type, 0.0)

    raw_score = (
        0.34 * content_score
        + 0.28 * impact_score
        + 0.16 * scope_score
        + 0.10 * source_quality
        + 0.07 * novelty_score
        + 0.05 * type_boost
        - low_value_penalty
    )

    final_score = raw_score * evidence_multiplier
    if is_quote_lead:
        final_score *= 0.65
    if is_low_editorial:
        final_score = min(final_score, 20.0)

    final_score = max(0.0, min(100.0, round(final_score, 2)))

    debug: dict[str, Any] = {
        "event_type": event_type,
        "scope": scope_label,
        "content": round(content_score, 2),
        "impact": round(impact_score, 2),
        "scope_score": round(scope_score, 2),
        "evidence_multiplier": round(evidence_multiplier, 2),
        "novelty": round(novelty_score, 2),
        "source_quality": round(source_quality, 2),
        "type_boost": round(type_boost, 2),
        "penalty": round(low_value_penalty, 2),
        "publishers": unique_publishers,
        "strong_hits": strong_hits,
        "moderate_hits": moderate_hits,
        "magnitude_hits": magnitude_hits,
        "is_quote_lead": is_quote_lead,
        "is_listicle": is_listicle,
        "is_announcement": is_announcement,
        "is_review": is_review,
        "critical": False,
        "reasons": [],
    }

    if is_low_editorial:
        debug["reasons"].append("listicle/announcement/review content, capped")
    if is_quote_lead:
        debug["reasons"].append("quote-led headline, likely feature/opinion")
    if strong_hits:
        debug["reasons"].append(f"{event_type.replace('_', ' ')} signal ({strong_hits} strong terms)")
    if magnitude_hits:
        debug["reasons"].append("concrete magnitude/casualty figures present")
    if scope_label in {"global", "national"}:
        debug["reasons"].append(f"{scope_label} scope")
    if unique_publishers >= 3:
        debug["reasons"].append("multiple publishers corroborate the story")
    elif unique_publishers <= 1:
        debug["reasons"].append("single source, score dampened")
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

    title_lowered = _normalize_text(event.title)
    critical_re = _wb_pattern({"war", "terror", "election", "crisis", "pandemic"})
    event.is_critical = score >= 90.0 and bool(critical_re.search(title_lowered))
    return debug
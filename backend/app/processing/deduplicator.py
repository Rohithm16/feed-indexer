"""Event clustering with embedding cosine similarity + lexical/entity signals.

Adds to the previous lexical-only version:
- Semantic matching via embeddings + cosine similarity, so paraphrased
  coverage of the same story ("wildfire forces evacuations" vs "blaze
  prompts residents to flee") matches even with near-zero word overlap.
- A cheap fast-path for near-identical titles (wire-service syndication),
  so you don't spend an embedding call on the easy cases.
- Graceful degradation: if the embedding call fails, scoring falls back
  to the lexical/entity/title signals only, with weights renormalized
  rather than silently zeroing out 40% of the score.

Embeddings are computed locally with sentence-transformers
(all-MiniLM-L6-v2, 384 dims) -- no API key, no network call, no rate
limits. Well suited to short text like headlines/descriptions.

Storage: embeddings are stored as a plain JSON column (see
app.models.types.EmbeddingType), not pgvector -- no Postgres extension
required. Candidate retrieval is a category + time-window scan pulled
into Python, then scored/compared there; at this project's scale that's
simpler to run than an in-database ANN index and plenty fast. If the
event volume ever grows large enough for the Python-side scan to become
a bottleneck, switching Event.embedding to a pgvector column and adding
an ORDER BY embedding <=> ... query in _get_candidate_events is the
natural next step, but isn't needed yet.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.article import Article
from app.models.event import Event

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "the", "and", "for", "was", "were", "with", "from", "have", "has",
    "had", "this", "that", "these", "those", "said", "says", "after",
    "before", "would", "could", "should", "also", "more", "than", "into",
    "over", "under", "about", "amid", "amidst", "its", "his", "her",
    "their", "them", "they", "you", "your", "our", "who", "what", "when",
    "where", "why", "how", "will", "can", "may", "not", "but", "are",
    "been", "being", "new", "now", "one", "two", "per", "via", "off",
    "out", "all", "any", "some", "such", "each", "other", "then",
    "there", "here", "just", "still", "yet", "amp", "according",
    "report", "reports", "reported", "news", "day", "week", "year",
    "month", "latest", "top", "breaking",
}

_SUFFIX_RE = re.compile(r"(ing|edly|ed|es|s)$")

_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384


def _stem(token: str) -> str:
    if len(token) > 5:
        stripped = _SUFFIX_RE.sub("", token)
        if len(stripped) >= 3:
            return stripped
    return token


def _normalize_words(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {_stem(t) for t in tokens if len(t) > 2 and t not in _STOPWORDS}


def _extract_entities(text: str) -> set[str]:
    text = re.sub(r"(^|[.!?]\s+)([A-Z])", lambda m: m.group(1) + m.group(2).lower(), text)
    runs = re.findall(r"\b[A-Z][a-zA-Z.]*(?:\s+[A-Z][a-zA-Z.]*)*\b", text)
    return {r.strip().lower() for r in runs if len(r.strip()) > 2 and r.strip().lower() not in _STOPWORDS}


def _build_text(title: str, description: str | None) -> str:
    parts = [title]
    if description:
        parts.append(description)
    return " ".join(parts)


def _normalize_title_key(title: str) -> str:
    """Aggressively normalized title for fast-path exact/near-exact matching
    (catches syndicated wire copy where outlets run the identical headline).
    """
    words = sorted(_normalize_words(title))
    return " ".join(words)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


# --------------------------------------------------------------------------
# Embeddings
# --------------------------------------------------------------------------

_embedding_model = None


def _get_model():
    """Lazily load the local embedding model once per process.

    all-MiniLM-L6-v2: 384 dims, ~80MB, runs fine on CPU, well suited to
    short text (headlines/descriptions) -- no API key, no network call,
    no rate limits. First call downloads and caches the model weights
    (~90MB) to the local sentence-transformers cache dir; subsequent
    calls just load from disk.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL)
    return _embedding_model


def get_embedding(text: str) -> list[float] | None:
    """Compute an embedding for the given text using a local model."""
    if not text or not text.strip():
        return None
    try:
        model = _get_model()
        vector = model.encode(text[:8000], normalize_embeddings=True)
        return vector.tolist()
    except Exception:
        logger.warning("Local embedding failed, falling back to lexical-only scoring", exc_info=True)
        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _average_embedding(existing: list[float] | None, existing_count: int, new: list[float]) -> list[float]:
    """Running average so an event's embedding stays representative as more
    articles merge into it, without needing to re-embed the whole cluster.
    """
    if not existing or existing_count <= 0:
        return new
    total = existing_count + 1
    return [(e * existing_count + n) / total for e, n in zip(existing, new)]


# --------------------------------------------------------------------------
# Candidate retrieval
# --------------------------------------------------------------------------

def _get_candidate_events(db: Session, embedding: list[float] | None, category: str | None) -> list[Event]:
    """Pull candidate events from the dedup window, scoped by category when
    we have one to avoid a full unfiltered scan. The embedding itself isn't
    used for retrieval (no ANN index without pgvector) -- it's passed
    through to _agreement_score, where cosine similarity is computed in
    plain Python against each candidate's stored embedding.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.dedup_window_hours)
    query = db.query(Event).filter(Event.first_seen_at >= cutoff)
    if category:
        query = query.filter(Event.category == category)
    return query.all()


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def _agreement_score(
    article: Article,
    event: Event,
    article_embedding: list[float] | None,
) -> float:
    if not event.title and not event.summary:
        return 0.0

    article_text = _build_text(article.title, article.description)
    event_text = _build_text(event.title or "", event.summary or "")

    article_words = _normalize_words(article_text)
    event_words = _normalize_words(event_text)
    word_overlap = len(article_words & event_words) / max(1, len(article_words | event_words))

    article_title_words = _normalize_words(article.title or "")
    event_title_words = _normalize_words(event.title or "")
    title_overlap = len(article_title_words & event_title_words) / max(
        1, len(article_title_words | event_title_words)
    )

    article_entities = _extract_entities(article_text)
    event_entities = _extract_entities(event_text)
    if article_entities or event_entities:
        entity_overlap = len(article_entities & event_entities) / max(
            1, len(article_entities | event_entities)
        )
    else:
        entity_overlap = 0.0

    recency = 1.0
    article_time = _normalize_datetime(article.published_at)
    event_time = _normalize_datetime(event.last_updated_at)
    if article_time and event_time:
        age_hours = abs((article_time - event_time).total_seconds()) / 3600
        recency = max(0.0, 1.0 - min(age_hours / 24.0, 1.0))

    category_match = bool(article.category and event.category and article.category == event.category)

    cosine_sim = None
    if article_embedding is not None and getattr(event, "embedding", None) is not None:
        cosine_sim = _cosine_similarity(article_embedding, list(event.embedding))

    if cosine_sim is not None:
        score = (
            cosine_sim * 0.40
            + entity_overlap * 0.20
            + word_overlap * 0.15
            + title_overlap * 0.10
            + recency * 0.10
            + (0.05 if category_match else 0.0)
        )
    else:
        # No embedding available for this pair -- renormalize weights over
        # the remaining signals instead of just losing 40% of the score.
        score = (
            entity_overlap * 0.34
            + word_overlap * 0.25
            + title_overlap * 0.17
            + recency * 0.16
            + (0.08 if category_match else 0.0)
        )

    # Category is a static tag copied from whichever RSS feed the article
    # came from (e.g. NPR's feed says "national", Al Jazeera's says
    # "world" for the exact same earthquake) -- it's a source-labeling
    # quirk, not a reliable signal that two articles describe different
    # events. A hard penalty here was the confirmed cause of a real
    # earthquake story failing to dedup: it dropped an otherwise-strong
    # match below threshold purely because of inconsistent feed tagging.
    # Country is more reliable (two stories about disasters in different
    # countries really are different events), so that penalty stays.
    if article.country and event.country and article.country != event.country:
        score *= 0.3

    return score


def find_matching_event(
    article: Article,
    candidate_events: list[Event],
    threshold: float,
    article_embedding: list[float] | None,
) -> Event | None:
    if not candidate_events:
        return None

    # Fast path: near-identical normalized title (syndicated wire copy).
    article_key = _normalize_title_key(article.title or "")
    if article_key:
        for event in candidate_events:
            if article_key == _normalize_title_key(event.title or ""):
                logger.debug("Fast-path exact-title match: %s -> event %s", article.title[:60], event.id)
                return event

    best_event: Event | None = None
    best_score = 0.0
    for event in candidate_events:
        score = _agreement_score(article, event, article_embedding)
        if score > best_score:
            best_score = score
            best_event = event

    if best_event and best_score >= threshold:
        logger.debug("Matched %s to event %s with score %.2f", article.title[:60], best_event.id, best_score)
        return best_event
    return None


def get_or_create_event(article: Article, db: Session) -> Event:
    article_text = _build_text(article.title, article.description or "")
    article_embedding = get_embedding(article_text)

    candidates = _get_candidate_events(db, article_embedding, category=article.category)
    match = find_matching_event(article, candidates, settings.similarity_threshold, article_embedding)

    if match:
        match.last_updated_at = datetime.now(timezone.utc)
        match.article_count = (match.article_count or 1) + 1
        if article_embedding is not None:
            existing = list(match.embedding) if getattr(match, "embedding", None) is not None else None
            match.embedding = _average_embedding(existing, (match.article_count or 2) - 1, article_embedding)
        return match

    new_event = Event(
        title=article.title,
        category=article.category,
        country=article.country,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        embedding=article_embedding,
        article_count=1,
    )
    db.add(new_event)
    db.flush()
    return new_event
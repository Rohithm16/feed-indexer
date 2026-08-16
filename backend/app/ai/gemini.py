"""
Gemini AI analysis module.

Takes a list of articles from a clustered event and asks Gemini to generate:
- A canonical event title
- A 2-3 sentence objective summary
- A "why it matters" explanation
- An importance score (0-100)
- A critical flag (wars, disasters, major legislation, etc.)
- Category and tags

We use gemini-3.5-flash-lite for speed and low cost.
The response is strict JSON — no markdown wrappers.
"""

import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.models.article import Article

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

# Categories Gemini can assign
VALID_CATEGORIES = {
    "world", "national", "technology", "business",
    "science", "politics", "finance", "health",
}

# These keywords in Gemini's output indicate a critical event
CRITICAL_CATEGORIES_HINT = (
    "natural disaster, earthquake, hurricane, flood, wildfire, "
    "war, conflict, military, invasion, "
    "terror attack, bombing, shooting, "
    "major legislation, supreme court, "
    "tax change, banking crisis, financial crisis, "
    "public safety, pandemic, outbreak"
)


def _build_prompt(articles: list[Article]) -> str:
    """Build the prompt for Gemini from the article list."""
    titles = "\n".join(f"- {a.title}" for a in articles[:10])  # cap at 10 titles
    descriptions = "\n".join(
        f"- {a.description[:300]}"
        for a in articles[:5]
        if a.description
    )

    return f"""You are an objective news editor. Analyze these news articles about the same event.

ARTICLE TITLES:
{titles}

ARTICLE DESCRIPTIONS (sample):
{descriptions}

Respond with ONLY valid JSON — no markdown, no code fences, no extra text.
Use this exact structure:
{{
  "title": "clear, factual, specific event title (max 120 chars)",
  "summary": "2-3 sentence objective summary of what happened",
  "why_it_matters": "1-2 sentences on the broader significance for society or the reader",
  "importance_score": <integer 0-100 based on: scale of impact, lives affected, geopolitical significance, policy implications. 90-100=global crisis, 70-89=major national event, 50-69=significant regional, 30-49=notable, 0-29=routine>,
  "is_critical": <true ONLY if event involves: {CRITICAL_CATEGORIES_HINT}>,
  "category": "<one of: world, national, technology, business, science, politics, finance, health>",
  "tags": ["tag1", "tag2", "tag3"]
}}"""


def analyze_event(articles: list[Article]) -> Optional[dict]:
    """
    Call Gemini to analyze a clustered event.
    Returns a dict with the analysis fields, or None if the call fails.
    """
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set — skipping AI analysis")
        return None

    if not articles:
        return None

    prompt = _build_prompt(articles)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            ),
        )
        if not response.text:
            logger.error("Gemini returned an empty response.")
            return None
        raw = response.text.strip()

        # Strip any accidental markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)

        # Sanitize category
        if data.get("category") not in VALID_CATEGORIES:
            data["category"] = articles[0].category or "world"

        # Ensure importance_score is in range
        score = int(data.get("importance_score", 50))
        data["importance_score"] = max(0, min(100, score))

        return data

    except json.JSONDecodeError as exc:
        logger.error(f"Gemini returned invalid JSON: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Gemini API error: {exc}")
        return None


def apply_analysis_to_event(event, analysis: dict) -> None:
    """
    Write Gemini's language-generation fields onto an Event model instance.

    Intentionally does NOT touch importance_score, is_critical, or category:
    those are locally computed by app.ranking.scorer.apply_scoring_to_event
    and must stay that way (see the "Gemini must not own these decisions"
    comment on the Event model). Gemini is still asked to estimate these in
    its own JSON output -- that's kept for now because reasoning about scale
    of impact tends to make its title/summary/why_it_matters phrasing better
    calibrated -- but the estimate itself is discarded here rather than
    applied to the event.

    Modifies the event in-place; caller is responsible for committing.
    """
    event.title = analysis.get("title", event.title)
    event.summary = analysis.get("summary")
    event.why_it_matters = analysis.get("why_it_matters")
    event.tags = analysis.get("tags", [])
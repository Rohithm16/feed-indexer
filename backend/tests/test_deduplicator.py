from datetime import datetime, timezone

from app.models.article import Article
from app.models.event import Event
from app.processing.deduplicator import _agreement_score


def test_agreement_score_handles_mixed_datetime_timezones() -> None:
    article = Article(
        title="Global summit begins",
        description="Leaders gather for the annual summit.",
        url="https://example.com/1",
        source_name="Example News",
    )
    article.published_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    event = Event(
        title="Global summit begins",
        summary="Leaders gather for the annual summit.",
        last_updated_at=datetime(2025, 1, 1, 11, 0),
    )

    score, category_match = _agreement_score(article, event)

    assert score > 0.0
    assert category_match is False

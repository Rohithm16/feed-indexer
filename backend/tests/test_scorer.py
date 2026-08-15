from app.models.article import Article
from app.models.event import Event
from app.ranking.scorer import score_event


def test_score_event_works_with_article_and_event_text() -> None:
    article = Article(
        title="Ukraine says air defenses intercepted missiles overnight",
        description="Officials reported widespread damage after a major attack.",
        url="https://example.com/1",
        source_name="Example News",
    )
    event = Event(
        title="Ukraine attacks escalate",
        summary="A major incident unfolded across the region.",
    )

    score, debug = score_event(event, [article])

    assert 0.0 <= score <= 100.0
    assert debug["event_type"] in {"conflict", "terrorism", "disaster", "local"}

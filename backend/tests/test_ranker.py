from app.models.event import Event
from app.models.user_prefs import UserPreferences
from app.ranking.ranker import section_events


def test_section_events_uses_city_level_location_matches() -> None:
    chicago_event = Event(
        title="Chicago mayor announces transit plan",
        category="national",
        country="us",
        importance_score=62.0,
    )
    national_event = Event(
        title="Washington lawmakers debate budget",
        category="national",
        country="us",
        importance_score=60.0,
    )
    prefs = UserPreferences(country="us", city="Chicago")

    sections = section_events([national_event, chicago_event], prefs)

    assert [item[0].title for item in sections["local"]] == ["Chicago mayor announces transit plan"]
    assert [item[0].title for item in sections["national"]] == ["Washington lawmakers debate budget"]

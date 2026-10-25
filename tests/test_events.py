import json
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from squad import campus_events, events
from squad.config import Settings
from squad.events import EventsUnavailable, price_from_text, to_event, upcoming_events
from tests.fakes import TZ, make_event

NOW = datetime(2026, 10, 26, 8, 0, tzinfo=TZ)


@pytest.fixture
def settings(tmp_path):
    return replace(
        Settings(discord_token="", anthropic_api_key="", gemini_api_key=""),
        data_dir=tmp_path,
    )


@pytest.fixture
def feed_down(monkeypatch):
    def fail(url, quiet=False):
        raise SystemExit(4)

    monkeypatch.setattr(campus_events, "fetch", fail)


def write_cache(settings, fetched_at, items):
    path = settings.data_dir / "events_cache.json"
    path.write_text(
        json.dumps(
            {
                "fetched_at": fetched_at.isoformat(),
                "events": [e.model_dump(mode="json") for e in items],
            }
        )
    )


def test_price_from_text():
    assert price_from_text("Tickets $12 at door") == 12.0
    assert price_from_text("$7.50 entry") == 7.5
    assert price_from_text("Free pizza") == 0.0


def test_to_event_sets_two_hour_end_and_stable_id():
    raw = {
        "title": "Paint Night",
        "start": datetime(2026, 10, 28, 18, 0, tzinfo=TZ),
        "location": "MU 202, Tempe Campus",
        "org": "Art Club",
        "description": "Canvas included, $5 entry",
        "tags": ["Social"],
        "free_food": False,
        "url": "https://x.test/1",
    }
    one, two = to_event(raw), to_event(dict(raw))
    assert one.end - one.start == timedelta(hours=2)
    assert one.id == two.id == make_event("Paint Night", raw["start"]).id
    assert one.price_usd == 5.0


async def test_upcoming_events_uses_sample_feed(settings, monkeypatch):
    sample = campus_events.SAMPLE.read_text()
    monkeypatch.setattr(campus_events, "fetch", lambda url, quiet=False: sample)
    found = await upcoming_events(settings, NOW)
    assert len(found) >= 3
    assert all(e.start.tzinfo is not None and e.start > NOW for e in found)
    assert (settings.data_dir / "events_cache.json").exists()


async def test_stale_cache_served_when_feed_fails(settings, feed_down):
    cached = make_event("Cached Open Mic", NOW + timedelta(days=1))
    gone = make_event("Already Over", NOW - timedelta(hours=3))
    write_cache(settings, NOW - timedelta(hours=10), [cached, gone])
    found = await upcoming_events(settings, NOW)
    assert [e.id for e in found] == [cached.id]


async def test_no_cache_raises(settings, feed_down):
    with pytest.raises(EventsUnavailable):
        await upcoming_events(settings, NOW)


async def test_cache_older_than_48h_raises(settings, feed_down):
    write_cache(
        settings,
        NOW - timedelta(hours=49),
        [make_event("Old", NOW + timedelta(days=1))],
    )
    with pytest.raises(EventsUnavailable):
        await upcoming_events(settings, NOW)


async def test_memory_cache_skips_second_fetch(settings, monkeypatch):
    sample = campus_events.SAMPLE.read_text()
    calls = []

    def fetch(url, quiet=False):
        calls.append(url)
        return sample

    monkeypatch.setattr(campus_events, "fetch", fetch)
    first = await upcoming_events(settings, NOW)
    second = await upcoming_events(settings, NOW + timedelta(hours=1))
    assert len(calls) == 1 and second and len(second) <= len(first)
    events._memory.clear()

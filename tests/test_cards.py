from datetime import datetime

from discord import ui

from squad.models import Car, Plan, Rides
from squad.ui.cards import plan_card, results_card, who_line
from tests.fakes import TZ, make_event


def _plan(**overrides) -> Plan:
    data = {
        "id": "p1",
        "channel_id": "c1",
        "event": make_event(url="https://example.com/e", price_usd=5, free_food=True),
        "headline": "Open mic, then tacos",
        "why": "Everyone likes music.",
        "tradeoffs": ["Starts a bit late for Leo"],
        "created_at": datetime(2026, 10, 25, 12, tzinfo=TZ),
    }
    data.update(overrides)
    return Plan(**data)


def _texts(view: ui.LayoutView) -> list[str]:
    return [c.content for c in view.walk_children() if isinstance(c, ui.TextDisplay)]


def test_plan_card_contains_title_time_and_buttons():
    view = plan_card(_plan(), {"u1": "Maya"}, TZ)
    texts = _texts(view)
    assert texts[0] == "## 🗺️ This week's side quest"
    assert "### Open Mic Night" in texts
    assert any("<t:" in t for t in texts)
    assert "📍 Memorial Union 202, Tempe Campus · $5 · free food 🍕" in texts
    assert "**Trade-offs**\n• Starts a bit late for Leo" in texts
    assert texts[-1] == "Nobody's voted yet, no pressure 🙂"
    ids = [getattr(c, "custom_id", None) for c in view.walk_children()]
    assert "squad:close:p1" in ids
    assert "squad:why:p1" in ids
    urls = [getattr(c, "url", None) for c in view.walk_children()]
    assert "https://example.com/e" in urls


def test_who_line_hides_no_names():
    plan = _plan(votes={"u1": "yes", "u2": "maybe", "u3": "no"})
    line = who_line(plan, {"u1": "Maya", "u2": "Jordan", "u3": "Priya"})
    assert line == "✅ Maya  🤔 Jordan  ❌ 1 can't make it"
    assert "Priya" not in line
    assert who_line(_plan(votes={"u1": "yes"}), {"u1": "Maya"}) == "✅ Maya"


def test_results_card_rides_lines():
    plan = _plan(
        votes={"a": "yes", "b": "yes", "c": "yes", "d": "yes"},
        discord_event_url="https://discord.com/events/1/2",
    )
    rides = Rides(
        cars=[Car(driver_id="a", rider_ids=["b"]), Car(driver_id="c", rider_ids=[])],
        transit_ids=["d"],
        transit_tip="Valley Metro Rail to Veterans Way/College Ave.",
    )
    names = {"a": "Maya", "b": "Jordan", "c": "Priya", "d": "Leo"}
    texts = _texts(results_card(plan, names, rides, TZ))
    assert texts[0] == "## 🎉 It's on"
    assert "**Going:** Maya, Jordan, Priya, Leo" in texts
    body = "\n".join(texts)
    assert "**Rides**" in body
    assert "🚗 Maya → Jordan" in body
    assert "🚗 Priya → driving solo" in body
    assert "🚆 Leo: Valley Metro Rail to Veterans Way/College Ave." in body
    assert "📅 [Discord event](https://discord.com/events/1/2)" in body

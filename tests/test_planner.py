from datetime import datetime, timedelta

from squad.agents import DecisionOut, StanceOut, StancesOut
from squad.models import NoPlan, Plan, Request
from squad.planner import build_plan, pick_candidates
from tests.fakes import TZ, make_event, make_member

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=TZ)


def stances(*pairs, reason=""):
    return StancesOut(
        stances=[
            StanceOut(event_id=e.id, score=s, shared_reason=reason, flex_ok=False)
            for e, s in pairs
        ]
    )


async def plan(fake_llm, members, events, **kw):
    return await build_plan(
        members=members,
        events=events,
        busy={},
        request=Request(),
        llm=fake_llm,
        now=kw.pop("now", NOW),
        channel_id="c1",
        tz=TZ,
        **kw,
    )


async def test_no_members_no_plan(fake_llm):
    out = await plan(fake_llm, [], [make_event()])
    assert out == NoPlan(
        reason="Nobody's in the squad yet. Try /squad join or /squad demo."
    )


async def test_no_candidates_no_plan(fake_llm):
    out = await plan(fake_llm, [make_member()], [])
    assert out == NoPlan(reason="Nothing on Sun Devil Central fits this week.")


async def test_everyone_fits_status_polling(fake_llm):
    event = make_event()
    fake_llm.push(StancesOut, stances((event, 8)))
    fake_llm.push(StancesOut, stances((event, 7)))
    fake_llm.push(
        DecisionOut,
        DecisionOut(event_id=event.id, headline="Open mic!", why="Music", tradeoffs=[]),
    )
    out = await plan(fake_llm, [make_member("u1"), make_member("u2")], [event])
    assert isinstance(out, Plan)
    assert out.status == "polling"
    assert out.ask_first == []
    assert out.event == event
    assert out.channel_id == "c1"
    assert out.created_at == NOW
    assert len(out.id) == 10


async def test_conflict_sets_ask_first_from_code_not_model(fake_llm):
    free = make_event("Board Game Night")
    paid = make_event("Jazz Concert", price_usd=15)
    members = [make_member("u1"), make_member("u2", budget_usd=10)]
    fake_llm.push(StancesOut, stances((free, 3), (paid, 9)))
    fake_llm.push(StancesOut, stances((free, 3), (paid, 9)))
    fake_llm.push(
        DecisionOut,
        DecisionOut(event_id=paid.id, headline="Jazz", why="Music", tradeoffs=[]),
    )
    out = await plan(fake_llm, members, [free, paid])
    assert out.event.id == paid.id
    assert out.ask_first == ["u2"]
    assert out.status == "confirming"


async def test_exclude_skips_declined_event(fake_llm):
    first = make_event("Open Mic Night")
    second = make_event("Open Mic Night 2", start=first.start + timedelta(days=1))
    out = await plan(fake_llm, [make_member()], [first, second], exclude={first.id})
    assert out.event.id == second.id


async def test_drops_events_starting_within_90_minutes(fake_llm):
    soon = make_event("Open Mic Night")
    later = make_event("Open Mic Night 2", start=soon.start + timedelta(days=1))
    now = soon.start - timedelta(minutes=60)
    out = await plan(fake_llm, [make_member()], [soon, later], now=now)
    assert out.event.id == later.id
    assert isinstance(await plan(fake_llm, [make_member()], [soon], now=now), NoPlan)


async def test_llm_down_still_plans(fake_llm):
    event = make_event()
    out = await plan(fake_llm, [make_member("u1"), make_member("u2")], [event])
    assert isinstance(out, Plan)
    assert out.headline == "Open Mic Night, Fri 7:00 PM"
    assert [t.speaker for t in out.turns] == ["Coordinator"]


async def test_turns_never_contain_private_detail(fake_llm):
    event = make_event(price_usd=15)
    members = [make_member("u1"), make_member("u2", budget_usd=10)]
    fake_llm.push(StancesOut, stances((event, 8), reason="Live music, yes please"))
    fake_llm.push(StancesOut, stances((event, 6), reason="Could be fun"))
    fake_llm.push(
        DecisionOut,
        DecisionOut(
            event_id=event.id,
            headline="Open mic",
            why="Most of you love music",
            tradeoffs=[],
        ),
    )
    out = await plan(fake_llm, members, [event])
    assert [(t.speaker, t.member_id) for t in out.turns] == [
        ("U1's agent", "u1"),
        ("U2's agent", "u2"),
        ("Coordinator", None),
    ]
    assert out.turns[-1].text == "Most of you love music"
    for t in out.turns:
        assert "cap" not in t.text and "$" not in t.text


def test_pick_candidates_sorts_fewest_violations_then_interest():
    music = make_event("Live Music Jam")
    plain = make_event("Study Hall", start=music.start + timedelta(hours=1))
    pricey = make_event("Concert Gala", price_usd=50)
    out = pick_candidates(
        [make_member()], [pricey, plain, music], {}, Request(), TZ, set()
    )
    assert [e.id for e, _ in out] == [music.id, plain.id, pricey.id]
    assert out[2][1][0].kind == "budget"

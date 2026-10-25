from datetime import datetime, timedelta

from squad.agents import DecisionOut, StanceOut, StancesOut
from squad.models import BusyBlock, NoPlan, Plan, Request
from squad.planner import build_plan, find_match, pick_candidates
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


def _busy_during(event):
    return [BusyBlock(start=event.start, end=event.end)]


def test_find_match_everyone():
    mic = make_event("Open Mic Night")
    members = [make_member("u1"), make_member("u2")]
    assert find_match(members, [mic], {}, TZ, NOW, set()) == (mic, members)


def test_find_match_everyone_allows_budget_but_not_calendar():
    mic = make_event("Open Mic Night", price_usd=5)
    broke = make_member("u2", budget_usd=0)
    members = [make_member("u1"), broke]
    assert find_match(members, [mic], {}, TZ, NOW, set()) == (mic, members)
    busy = {"u2": _busy_during(mic)}
    assert find_match(members, [mic], busy, TZ, NOW, set()) is None


def test_find_match_subset_when_one_member_is_busy():
    gig = make_event("Open Mic Night with free pizza")
    fans = [make_member(i, interests=["music", "food"]) for i in ("u1", "u2")]
    busy_one = make_member("u3")
    out = find_match(
        [*fans, busy_one], [gig], {"u3": _busy_during(gig)}, TZ, NOW, set()
    )
    assert out == (gig, fans)


def test_find_match_none_when_nothing_qualifies():
    talk = make_event("Chemistry Seminar")
    assert (
        find_match([make_member("u1"), make_member("u2")], [talk], {}, TZ, NOW, set())
        is None
    )


def test_find_match_skips_events_within_6_hours():
    soon = make_event("Open Mic Night", start=NOW + timedelta(hours=5))
    later = make_event("Open Mic Night", start=NOW + timedelta(hours=7))
    members = [make_member("u1"), make_member("u2")]
    assert find_match(members, [soon], {}, TZ, NOW, set()) is None
    assert find_match(members, [soon, later], {}, TZ, NOW, set()) == (later, members)


def test_find_match_respects_exclude_and_prefers_everyone():
    mic = make_event("Open Mic Night")
    gig = make_event("Jam with free pizza", start=NOW + timedelta(days=1, hours=7))
    members = [
        make_member("u1", interests=["music", "food"]),
        make_member("u2", interests=["music", "food"]),
        make_member("u3"),
    ]
    busy = {"u3": _busy_during(gig)}
    # gig is earlier and scores higher but is only a subset match
    assert find_match(members, [gig, mic], busy, TZ, NOW, set()) == (mic, members)
    assert find_match(members, [gig, mic], busy, TZ, NOW, {mic.id}) == (
        gig,
        members[:2],
    )

from datetime import datetime, timedelta

from squad.agents import (
    DecisionOut,
    LearnedOut,
    RequestOut,
    StanceOut,
    StancesOut,
    coordinate,
    fallback_decision,
    learn_from_no,
    member_stances,
    parse_request,
)
from squad.llm import LLMError
from squad.models import Request, Stance, Violation
from tests.fakes import TZ, make_event, make_member

NOW = datetime(2026, 10, 26, 12, 0, tzinfo=TZ)


def budget_violation(member_id="u2"):
    return Violation(
        member_id=member_id,
        kind="budget",
        detail_private="your cap is $10",
        label_public="a budget limit",
    )


async def test_parse_request_drops_unknown_no_go(fake_llm):
    fake_llm.push(
        RequestOut,
        RequestOut(vibe="chill", max_price=15, exclude_no_go=["parties", "clowns"]),
    )
    req = await parse_request(fake_llm, "something chill under $15, no clubs", NOW)
    assert req.exclude_no_go == ["parties"]
    assert req.max_price == 15
    assert isinstance(req, Request)
    assert "2026-10-26" in fake_llm.calls[-1]["user"]


async def test_parse_request_falls_back_on_error(fake_llm):
    fake_llm.push(RequestOut, LLMError("boom"))
    req = await parse_request(fake_llm, "anything fun", NOW)
    assert req == Request(vibe="anything fun")


async def test_member_stances_clamps_and_fills_missing(fake_llm):
    member = make_member("u1", interests=["music"])
    mic = make_event("Open Mic Night")
    yoga = make_event("Sunrise Yoga", start=mic.start + timedelta(days=1))
    fake_llm.push(
        StancesOut,
        StancesOut(
            stances=[
                StanceOut(
                    event_id=mic.id, score=14, shared_reason="x" * 200, flex_ok=True
                ),
                StanceOut(event_id="nope", score=5, shared_reason="?", flex_ok=False),
            ]
        ),
    )
    stances = await member_stances(fake_llm, member, [(mic, []), (yoga, [])], Request())
    assert [s.event_id for s in stances] == [mic.id, yoga.id]
    assert stances[0].score == 10
    assert len(stances[0].shared_reason) == 120
    assert stances[0].flex_ok is True
    assert stances[1] == Stance(
        member_id="u1", event_id=yoga.id, score=0, shared_reason="", flex_ok=False
    )
    assert fake_llm.calls[-1]["effort"] == "low"
    assert "Open Mic Night" in fake_llm.calls[-1]["user"]


async def test_member_stances_fallback_on_error(fake_llm):
    member = make_member("u1", interests=["music"])
    mic = make_event("Open Mic Night")
    stances = await member_stances(fake_llm, member, [(mic, [])], Request())
    assert stances == [
        Stance(
            member_id="u1", event_id=mic.id, score=3, shared_reason="", flex_ok=False
        )
    ]


async def test_coordinator_prompt_has_no_private_details(fake_llm):
    members = [make_member("u1", name="Ava"), make_member("u2", name="Ben")]
    mic = make_event("Open Mic Night")
    stances = [
        Stance(
            member_id="u1",
            event_id=mic.id,
            score=8,
            shared_reason="I'd love it",
            flex_ok=False,
        )
    ]
    fake_llm.push(
        DecisionOut,
        DecisionOut(event_id=mic.id, headline="Mic", why="Fun", tradeoffs=["a"] * 5),
    )
    decision = await coordinate(
        fake_llm, members, [(mic, [budget_violation()])], stances, Request()
    )
    user = fake_llm.calls[-1]["user"]
    assert "Ben: a budget limit" in user
    assert "your cap" not in user
    assert "Ava" in user and "I'd love it" in user
    assert fake_llm.calls[-1]["effort"] == "medium"
    assert decision.event_id == mic.id and len(decision.tradeoffs) == 3


async def test_coordinate_unknown_event_uses_fallback(fake_llm):
    members = [make_member("u1")]
    mic = make_event("Open Mic Night")
    fake_llm.push(
        DecisionOut, DecisionOut(event_id="ghost", headline="h", why="w", tradeoffs=[])
    )
    decision = await coordinate(fake_llm, members, [(mic, [])], [], Request())
    assert decision == fallback_decision(members, [(mic, [])], [])
    assert decision.event_id == mic.id


async def test_fallback_prefers_fewest_violations():
    members = [make_member("u1"), make_member("u2")]
    loud = make_event("Big Concert")
    quiet = make_event("Board Game Night", start=loud.start + timedelta(days=1))
    stances = [
        Stance(
            member_id="u1", event_id=loud.id, score=10, shared_reason="", flex_ok=False
        ),
        Stance(
            member_id="u1", event_id=quiet.id, score=2, shared_reason="", flex_ok=False
        ),
    ]
    candidates = [
        (loud, [budget_violation(), budget_violation("u1")]),
        (quiet, [budget_violation()]),
    ]
    decision = fallback_decision(members, candidates, stances)
    assert decision.event_id == quiet.id
    assert decision.headline == "Board Game Night, Sat 7:00 PM"
    assert decision.why == "It's the option that fits the most of you this week."
    assert decision.tradeoffs == ["Someone has a budget limit"]


async def test_learn_from_no_keep_false_returns_none(fake_llm):
    fake_llm.push(LearnedOut, LearnedOut(kind="note", value="sick", keep=False))
    out = await learn_from_no(fake_llm, make_member(), "I'm sick", make_event())
    assert out is None


async def test_learn_from_no_keep_true(fake_llm):
    fake_llm.push(LearnedOut, LearnedOut(kind="max_price", value="10", keep=True))
    out = await learn_from_no(fake_llm, make_member(), "x" * 300, make_event())
    assert out.kind == "max_price" and out.value == "10"
    assert len(out.source_text) == 140 and out.created_at.tzinfo is not None

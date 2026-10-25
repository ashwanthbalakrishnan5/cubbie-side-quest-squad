from datetime import datetime

import discord

from squad.config import Settings
from squad.personas import DEMO_VOTES, INTRO_LINES, PERSONAS, persona_busy, post_as
from tests.fakes import TZ


def test_four_personas_ids_and_seats():
    assert [(p.id, p.name, p.seats) for p in PERSONAS] == [
        ("demo:maya", "Maya", 0),
        ("demo:jordan", "Jordan", 3),
        ("demo:priya", "Priya", 0),
        ("demo:leo", "Leo", 1),
    ]
    assert all(p.is_demo for p in PERSONAS)
    by_id = {p.id: p for p in PERSONAS}
    assert by_id["demo:priya"].budget_usd == 0
    assert len(by_id["demo:priya"].free_slots) == 6
    assert by_id["demo:jordan"].no_go == ["late"]
    assert by_id["demo:leo"].no_go == []
    assert by_id["demo:maya"].avatar_url == (
        "https://api.dicebear.com/9.x/notionists/png?seed=Maya&size=128"
    )
    assert set(INTRO_LINES) == {"maya", "jordan", "priya", "leo"}


def test_persona_busy_is_relative_to_week():
    by_id = {p.id: p for p in PERSONAS}
    wednesday = datetime(2026, 10, 28, 15, 0, tzinfo=TZ)  # week of Mon 26 Oct
    (leo,) = persona_busy(by_id["demo:leo"], wednesday, TZ)
    assert leo.start == datetime(2026, 10, 30, 18, 0, tzinfo=TZ)
    assert leo.end == datetime(2026, 10, 30, 21, 0, tzinfo=TZ)
    (maya,) = persona_busy(by_id["demo:maya"], wednesday, TZ)
    assert maya.start == datetime(2026, 10, 31, 12, 0, tzinfo=TZ)
    assert maya.end == datetime(2026, 10, 31, 16, 0, tzinfo=TZ)
    assert persona_busy(by_id["demo:jordan"], wednesday, TZ) == []
    assert persona_busy(by_id["demo:priya"], wednesday, TZ) == []
    next_week = persona_busy(by_id["demo:leo"], datetime(2026, 11, 2, tzinfo=TZ), TZ)
    assert next_week[0].start == datetime(2026, 11, 6, 18, 0, tzinfo=TZ)


def test_demo_votes_cover_every_persona():
    assert set(DEMO_VOTES) == {p.id.removeprefix("demo:") for p in PERSONAS}
    delays = Settings("", "", "").persona_vote_delays_s
    assert sorted(i for i, _, _ in DEMO_VOTES.values()) == list(range(len(delays)))
    assert DEMO_VOTES["jordan"][1] == "no" and DEMO_VOTES["jordan"][2]
    assert DEMO_VOTES["leo"] == (2, "maybe", None)


class StubWebhook:
    def __init__(self):
        self.calls = []

    async def send(self, content, **kwargs):
        self.calls.append((content, kwargs))


async def test_post_as_passes_username_and_no_mentions():
    hook = StubWebhook()
    await post_as(hook, "Maya", "https://x/a.png", "hii")
    content, kw = hook.calls[0]
    assert content == "hii"
    assert kw["username"] == "Maya"
    assert kw["avatar_url"] == "https://x/a.png"
    assert kw["thread"] is discord.utils.MISSING
    am = kw["allowed_mentions"]
    assert not am.everyone and not am.users and not am.roles

    thread = discord.Object(id=42)
    await post_as(hook, "Leo", "u", "yo", thread=thread)
    assert hook.calls[1][1]["thread"] is thread

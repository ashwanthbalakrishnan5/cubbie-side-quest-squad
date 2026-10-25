from datetime import datetime, timedelta

import discord
import pytest

from squad.bot import SquadBot
from squad.config import Settings
from squad.flows import nudge_flow
from squad.models import Plan, Squad
from squad.personas import PERSONAS
from squad.voice.bridge import CallOutcome
from tests.fakes import TZ, make_event, make_member

CREATED = datetime(2026, 10, 28, 12, 0, tzinfo=TZ)
LATER = CREATED + timedelta(hours=1)  # past the 30 min nudge delay, not quiet hours


class Thread:
    id = 900

    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content=None, **kw):
        self.sent.append(content)


class Card:
    def __init__(self) -> None:
        self.edits: list = []

    async def edit(self, **kw):
        self.edits.append(kw["view"])


class Channel:
    id = 555
    name = "squad-chat"

    def __init__(self) -> None:
        self.sent: list[str] = []
        self.card = Card()

    async def send(self, content=None, **kw):
        self.sent.append(content)

    def get_partial_message(self, message_id: int):
        assert message_id == 101
        return self.card


def texts(view) -> list[str]:
    return [
        i.content for i in view.walk_children() if isinstance(i, discord.ui.TextDisplay)
    ]


@pytest.fixture
def channel():
    return Channel()


@pytest.fixture
def thread():
    return Thread()


async def make_bot(store, fake_llm, channel, thread, **settings):
    s = Settings(
        discord_token="x", anthropic_api_key="x", gemini_api_key="x", **settings
    )
    b = SquadBot(s, store, fake_llm, None)
    b.get_channel = {555: channel, 900: thread}.get
    nudge_flow.setup(b)
    return b


@pytest.fixture
async def bot(store, fake_llm, channel, thread):
    # unreachable sidecar: voice is configured but WhatsApp isn't paired
    b = await make_bot(
        store, fake_llm, channel, thread, wa_voice_url="http://127.0.0.1:1"
    )
    yield b
    b.flows.nudge_loop.cancel()


def fake_dm(bot, ok: bool) -> list[tuple]:
    dms = []

    async def dm(user_id, *, content=None, view=None):
        dms.append((user_id, content))
        return ok

    bot.dm = dm
    return dms


async def seed(store, *members) -> Plan:
    for m in members:
        await store.put_member(m)
    await store.put_squad(
        Squad(channel_id="555", guild_id="777", member_ids=[m.id for m in members])
    )
    plan = Plan(
        id="p1",
        channel_id="555",
        event=make_event(),
        status="polling",
        headline="Music night",
        why="Everyone likes music.",
        message_id="101",
        thread_id="900",
        created_at=CREATED,
    )
    await store.put_plan(plan)
    return plan


async def test_due_skips_voted_personas_quiet_and_already_nudged(bot, store):
    sleepy = make_member("4", name="Sleepy", quiet_hours="0-10")
    plan = await seed(
        store,
        make_member("1", name="Ada"),
        make_member("2", name="Bo"),
        make_member("3", name="Cy"),
        sleepy,
        PERSONAS[0],
    )
    plan.votes["2"] = "yes"
    plan.nudged.append("3")
    outsider = make_member("9")
    await store.put_member(outsider)
    plan.votes["9"] = "no"

    assert bot.flows.nudge_due(plan, CREATED + timedelta(minutes=29)) == []
    assert [m.id for m in bot.flows.nudge_due(plan, LATER)] == ["1", "4"]
    # 9am is inside Sleepy's midnight-10am quiet hours
    nine = datetime(2026, 10, 29, 9, 0, tzinfo=TZ)
    assert [m.id for m in bot.flows.nudge_due(plan, nine)] == ["1"]
    plan.status = "closed"
    assert bot.flows.nudge_due(plan, LATER) == []


async def test_nudge_once_per_plan(bot, store, channel):
    await seed(store, make_member("1", name="Ada"))
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)
    await bot.flows.nudge_tick(LATER + timedelta(minutes=5))

    assert [uid for uid, _ in dms] == ["1"]
    assert store.plan("p1").nudged == ["1"]


async def test_call_answer_sets_vote_and_posts_without_reason(
    store, fake_llm, channel, thread, monkeypatch
):
    bot = await make_bot(store, fake_llm, channel, thread)
    try:
        await seed(
            store,
            make_member("1", name="Ada", phone="+14805550123", call_opt_in=True),
            make_member("2", name="Bo"),
        )
        store.plan("p1").votes["2"] = "yes"
        calls = []

        async def connected(settings):
            return True

        async def call(settings, phone, name, plan, going_names):
            calls.append((phone, name, going_names))
            return CallOutcome(
                answered=True, answer="maybe", reason="my exam is Friday"
            )

        monkeypatch.setattr(nudge_flow, "voice_connected", connected)
        monkeypatch.setattr(nudge_flow, "nudge_call", call)
        dms = fake_dm(bot, ok=True)

        await bot.flows.nudge_tick(LATER)

        assert calls == [("+14805550123", "Ada", ["Bo"])]
        assert store.plan("p1").votes["1"] == "maybe"
        assert any("🤔 Ada" in t for t in texts(channel.card.edits[-1]))
        assert thread.sent == ["📞 Ada picked up and said maybe"]
        everything = thread.sent + channel.sent + texts(channel.card.edits[-1])
        assert not any("exam" in (t or "") for t in everything)
        assert dms == []
    finally:
        bot.flows.nudge_loop.cancel()


async def test_voice_off_falls_back_to_dm(bot, store, channel, monkeypatch):
    await seed(
        store, make_member("1", name="Ada", phone="+14805550123", call_opt_in=True)
    )

    async def call(*a, **kw):
        raise AssertionError("no call while WhatsApp is not connected")

    monkeypatch.setattr(nudge_flow, "nudge_call", call)
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)

    unix = int(make_event().start.timestamp())
    assert dms == [
        (
            "1",
            (
                f"Hey Ada 👋 the squad's planning Open Mic Night <t:{unix}:R>. "
                "You in? The poll's in #squad-chat."
            ),
        )
    ]
    assert channel.sent == []


async def test_unanswered_call_falls_back_to_dm(bot, store, monkeypatch):
    await seed(
        store, make_member("1", name="Ada", phone="+14805550123", call_opt_in=True)
    )

    async def connected(settings):
        return True

    async def call(*a, **kw):
        return CallOutcome(answered=False)

    monkeypatch.setattr(nudge_flow, "voice_connected", connected)
    monkeypatch.setattr(nudge_flow, "nudge_call", call)
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)

    assert [uid for uid, _ in dms] == ["1"]
    assert "1" not in store.plan("p1").votes


async def test_dm_forbidden_falls_back_to_channel_mention(bot, store, channel):
    await seed(store, make_member("1", name="Ada", budget_usd=0))
    fake_dm(bot, ok=False)

    await bot.flows.nudge_tick(LATER)

    assert channel.sent == ["<@1> psst, there's a poll waiting for you 🗺️"]


async def test_voice_connected_reads_status(monkeypatch):
    s = Settings(
        discord_token="x",
        anthropic_api_key="x",
        gemini_api_key="x",
        wa_voice_url="http://127.0.0.1:1",
    )
    assert await nudge_flow.voice_connected(s) is False
    blank = Settings(
        discord_token="x", anthropic_api_key="x", gemini_api_key="x", wa_voice_url=""
    )
    assert await nudge_flow.voice_connected(blank) is False


async def test_answered_call_after_poll_closed_sends_nothing(
    bot, store, channel, thread, monkeypatch
):
    await seed(
        store, make_member("1", name="Ada", phone="+14805550123", call_opt_in=True)
    )

    async def connected(settings):
        return True

    async def call(settings, phone, name, plan, going_names):
        plan.status = "closed"  # the poll closes while Ada is on the call
        return CallOutcome(answered=True, answer="yes")

    monkeypatch.setattr(nudge_flow, "voice_connected", connected)
    monkeypatch.setattr(nudge_flow, "nudge_call", call)
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)

    assert dms == []
    assert "1" not in store.plan("p1").votes
    assert thread.sent == [] and channel.sent == [] and channel.card.edits == []


async def test_unanswered_call_after_poll_closed_sends_nothing(
    bot, store, channel, monkeypatch
):
    await seed(
        store, make_member("1", name="Ada", phone="+14805550123", call_opt_in=True)
    )

    async def connected(settings):
        return True

    async def call(settings, phone, name, plan, going_names):
        plan.status = "closed"  # the poll closes while Ada's phone rings
        return CallOutcome(answered=False)

    monkeypatch.setattr(nudge_flow, "voice_connected", connected)
    monkeypatch.setattr(nudge_flow, "nudge_call", call)
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)

    assert dms == [] and channel.sent == []


async def test_poll_closed_during_one_call_skips_the_rest(
    bot, store, channel, monkeypatch
):
    await seed(
        store,
        make_member("1", name="Ada", phone="+14805550123", call_opt_in=True),
        make_member("2", name="Bo", phone="+14805550124", call_opt_in=True),
    )
    calls = []

    async def connected(settings):
        return True

    async def call(settings, phone, name, plan, going_names):
        calls.append((name, plan.status))
        plan.status = "closed"  # the poll closes during Ada's call
        return CallOutcome(answered=False)

    monkeypatch.setattr(nudge_flow, "voice_connected", connected)
    monkeypatch.setattr(nudge_flow, "nudge_call", call)
    dms = fake_dm(bot, ok=True)

    await bot.flows.nudge_tick(LATER)

    assert calls == [("Ada", "polling")]
    assert dms == [] and channel.sent == []

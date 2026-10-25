import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import discord
import pytest

from squad.agents import DecisionOut, StanceOut, StancesOut
from squad.bot import SquadBot
from squad.config import Settings
from squad.constants import VOTE_ANSWERS
from squad.events import EventsUnavailable
from squad.flows import plan_flow
from squad.models import Squad
from squad.personas import PERSONAS
from tests.fakes import TZ, make_event, make_member


def ahead(days: int, hour: int) -> datetime:
    day = datetime.now(TZ) + timedelta(days=days)
    return day.replace(hour=hour, minute=0, second=0, microsecond=0)


class Thread:
    id = 900

    def __init__(self, name: str) -> None:
        self.name = name
        self.sent: list = []

    async def send(self, content=None, **kw):
        self.sent.append(content)


class Message:
    def __init__(self, id: int, channel) -> None:
        self.id = id
        self.channel = channel

    async def create_thread(self, *, name: str):
        self.channel.threads.append(Thread(name))
        return self.channel.threads[-1]


class Webhook:
    url = "https://discord.com/api/webhooks/1/token"

    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))


class Channel:
    def __init__(self) -> None:
        self.id = 555
        self.guild = SimpleNamespace(id=777)
        self.sent: list[tuple] = []
        self.threads: list[Thread] = []
        self.webhook = Webhook()

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))
        return Message(100 + len(self.sent), self)

    async def create_webhook(self, *, name: str):
        return self.webhook


class Response:
    def __init__(self) -> None:
        self.sent: list = []

    async def send_message(self, content=None, **kw):
        self.sent.append((content, kw))

    async def edit_message(self, **kw):
        self.sent.append(("edit", kw))


def texts(view) -> list[str]:
    return [
        i.content for i in view.walk_children() if isinstance(i, discord.ui.TextDisplay)
    ]


def public_texts(channel: Channel) -> list[str]:
    out = []
    for content, kw in channel.sent:
        out += [content or ""] + (texts(kw["view"]) if "view" in kw else [])
        if "poll" in kw:
            out.append(kw["poll"].question)
    out += [content for content, _ in channel.webhook.sent]
    return out


@pytest.fixture
async def bot(store, fake_llm, monkeypatch):
    settings = Settings(discord_token="x", anthropic_api_key="x", gemini_api_key="x")
    b = SquadBot(settings, store, fake_llm, None)
    plan_flow.setup(b)
    yield b
    b.flows.weekly_loop.cancel()


def feed(monkeypatch, *events):
    async def upcoming(settings, now, days=7):
        return list(events)

    monkeypatch.setattr(plan_flow, "upcoming_events", upcoming)


def fake_dm(bot, answer: str | None) -> list[tuple]:
    """Records DMs; answer None = DMs closed, else the member clicks that button."""
    dms = []

    async def dm(user_id, *, content=None, view=None):
        dms.append((user_id, texts(view)[0]))
        if answer is None:
            return False
        ids = [getattr(i, "custom_id", None) or "" for i in view.walk_children()]
        plan_id = next(i for i in ids if i.startswith("squad:confirm:")).split(":")[2]
        click = SimpleNamespace(
            user=SimpleNamespace(id=int(user_id)), response=Response()
        )
        asyncio.get_running_loop().create_task(
            bot.flows.confirm(click, plan_id, answer)
        )
        return True

    bot.dm = dm
    return dms


async def seed(store, *members) -> Squad:
    for m in members:
        await store.put_member(m)
    squad = Squad(channel_id="555", guild_id="777", member_ids=[m.id for m in members])
    await store.put_squad(squad)
    return squad


async def test_feed_down_posts_friendly_message(bot, store, monkeypatch):
    async def down(settings, now, days=7):
        raise EventsUnavailable("Sun Devil Central isn't answering")

    monkeypatch.setattr(plan_flow, "upcoming_events", down)
    squad = await seed(store, make_member("1"))
    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())
    assert channel.sent == [
        ("Sun Devil Central isn't answering right now. I'll try again in a bit 🌵", {})
    ]
    assert store.plans() == []


async def test_happy_path_posts_card_thread_turns_and_poll(
    bot, store, fake_llm, monkeypatch
):
    event = make_event("Open Mic Night", start=ahead(1, 18))
    feed(monkeypatch, event)
    squad = await seed(
        store, make_member("1", name="Ash"), make_member("2", name="Sam")
    )
    for reason in ("I love open mics", "Sam's always down for music"):
        fake_llm.push(
            StancesOut,
            StancesOut(
                stances=[
                    StanceOut(
                        event_id=event.id, score=8, shared_reason=reason, flex_ok=False
                    )
                ]
            ),
        )
    fake_llm.push(
        DecisionOut,
        DecisionOut(
            event_id=event.id,
            headline="Mic night",
            why="Both of you love music.",
            tradeoffs=[],
        ),
    )
    scheduled = []
    bot.flows.schedule_persona_votes = scheduled.append

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    (_, card), (_, poll_kw) = channel.sent
    assert "### Open Mic Night" in texts(card["view"])
    poll = poll_kw["poll"]
    assert poll.question == "Open Mic Night, you in?"
    assert [a.text for a in poll.answers] == list(VOTE_ANSWERS)
    assert poll.duration == timedelta(hours=1)

    (thread,) = channel.threads
    assert thread.name == "🗺️ Open Mic Night"
    sent = channel.webhook.sent
    assert [kw["username"] for _, kw in sent] == [
        "Ash's agent",
        "Sam's agent",
        "Coordinator",
    ]
    assert [text for text, _ in sent][-1] == "Both of you love music."
    assert all(kw["thread"] is thread for _, kw in sent)

    (plan,) = store.plans("polling")
    assert (plan.message_id, plan.poll_message_id, plan.thread_id) == (
        "101",
        "102",
        "900",
    )
    assert plan.poll_closes_at is not None
    assert [p.id for p in scheduled] == [plan.id]
    assert store.squad("555").webhook_url == Webhook.url


async def test_conflict_dm_yes_then_posts(bot, store, monkeypatch):
    event = make_event("Pottery Night", start=ahead(1, 18), price_usd=5)
    feed(monkeypatch, event)
    squad = await seed(store, make_member("1"), make_member("2", budget_usd=0))
    dms = fake_dm(bot, "yes")

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    assert [uid for uid, _ in dms] == ["2"]
    assert dms[0][1].startswith(
        "Quick check before I post this week's plan: Pottery Night, <t:"
    )
    assert dms[0][1].endswith("Heads up: it's $5 and your cap is $0. Still up for it?")
    (plan,) = store.plans("polling")
    assert plan.event.id == event.id and plan.confirmations == {"2": True}
    assert "### Pottery Night" in texts(channel.sent[0][1]["view"])


async def test_conflict_dm_forbidden_counts_as_no_and_replans(
    bot, store, fake_llm, monkeypatch
):
    pricey = make_event("Pottery Night", start=ahead(1, 18), price_usd=5)
    free = make_event("Open Mic Night", start=ahead(2, 18))
    feed(monkeypatch, pricey, free)
    squad = await seed(store, make_member("1"), make_member("2", budget_usd=0))
    fake_llm.push(
        DecisionOut,
        DecisionOut(event_id=pricey.id, headline="h", why="w", tradeoffs=[]),
    )
    dms = fake_dm(bot, None)

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    assert [uid for uid, _ in dms] == ["2"]
    (plan,) = store.plans("polling")
    assert plan.event.id == free.id
    assert plan.declined_event_ids == [pricey.id]
    assert "### Open Mic Night" in texts(channel.sent[0][1]["view"])


async def test_three_declines_posts_no_plan(bot, store, monkeypatch):
    events = [
        make_event(f"Pottery Night {i}", start=ahead(i, 18), price_usd=5)
        for i in (1, 2, 3, 4)
    ]
    feed(monkeypatch, *events)
    squad = await seed(store, make_member("1"), make_member("2", budget_usd=0))
    dms = fake_dm(bot, None)

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    assert len(dms) == 3
    ((_, kw),) = channel.sent
    shown = texts(kw["view"])
    assert shown[:2] == ["## 🌙 No side quest this week", plan_flow.ALL_DECLINED]
    assert shown[2].startswith("Closest call: **Pottery Night 3**")
    assert store.plans() == []


async def test_persona_with_late_limit_declines_without_bothering_humans(
    bot, store, fake_llm, monkeypatch
):
    jordan = next(p for p in PERSONAS if p.id == "demo:jordan")
    late = make_event("Midnight Trivia", start=ahead(1, 21))
    early = make_event("Board Game Night", start=ahead(2, 18))
    feed(monkeypatch, late, early)
    squad = await seed(store, make_member("1"), jordan)
    fake_llm.push(
        DecisionOut, DecisionOut(event_id=late.id, headline="h", why="w", tradeoffs=[])
    )
    dms = fake_dm(bot, "yes")

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    assert dms == []
    (plan,) = store.plans("polling")
    assert plan.event.id == early.id and plan.declined_event_ids == [late.id]
    posted = [text for text, _ in channel.webhook.sent]
    assert "Jordan's agent checked with Jordan privately: not this one." in posted


async def test_weekly_loop_runs_once_per_day(bot, store, monkeypatch):
    squad = await seed(store, make_member("1"))
    squad.weekly_weekday, squad.weekly_hour = 2, 18
    await store.put_squad(squad)
    channel = Channel()
    monkeypatch.setattr(bot, "get_channel", lambda _id: channel)
    runs = []

    async def run_plan(squad, channel, request):
        runs.append(squad.channel_id)

    bot.flows.run_plan = run_plan

    async def tick(when: datetime) -> None:
        await bot.flows.weekly_tick(when)
        for _ in range(3):
            await asyncio.sleep(0)

    wed = datetime(2026, 10, 28, 18, 5, tzinfo=TZ)
    await tick(wed)
    await tick(wed + timedelta(minutes=1))
    await tick(wed + timedelta(days=1))  # Thursday: not due
    assert runs == ["555"]
    assert channel.sent == [(plan_flow.ON_IT, {})]
    assert store.squad("555").last_weekly_date == wed.date()

    await tick(wed + timedelta(days=7))
    assert runs == ["555", "555"]


async def test_card_and_turns_have_no_private_detail(bot, store, fake_llm, monkeypatch):
    maya = next(p for p in PERSONAS if p.id == "demo:maya")
    event = make_event("Pottery Night", start=ahead(1, 18), price_usd=25)
    feed(monkeypatch, event)
    squad = await seed(store, make_member("2", name="Sam", budget_usd=0), maya)
    for reason in ("pottery sounds fun", "Maya loves art"):
        fake_llm.push(
            StancesOut,
            StancesOut(
                stances=[
                    StanceOut(
                        event_id=event.id, score=7, shared_reason=reason, flex_ok=True
                    )
                ]
            ),
        )
    dms = fake_dm(bot, "yes")

    channel = Channel()
    await bot.flows.run_plan(squad, channel, plan_flow.Request())

    assert "your cap is $0" in dms[0][1]  # private detail goes only to that member
    public = "\n".join(public_texts(channel))
    assert "Maya's agent checked with Maya privately: all good." in public
    for private in ("cap", "your cap is", "you look busy"):
        assert private not in public
    (plan,) = store.plans("polling")
    assert plan.confirmations == {"demo:maya": True, "2": True}

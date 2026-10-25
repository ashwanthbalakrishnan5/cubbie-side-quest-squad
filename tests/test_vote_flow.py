import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import discord
import pytest

from squad.agents import LearnedOut
from squad.bot import SquadBot
from squad.config import Settings
from squad.flows import vote_flow
from squad.models import Plan, Squad
from squad.personas import PERSONAS
from tests.fakes import TZ, make_event, make_member

FORBIDDEN = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "")


def texts(view) -> list[str]:
    return [
        i.content for i in view.walk_children() if isinstance(i, discord.ui.TextDisplay)
    ]


class Msg:
    def __init__(self) -> None:
        self.edits: list = []
        self.ended = False

    async def edit(self, **kw):
        self.edits.append(kw)

    async def end_poll(self):
        self.ended = True


class Webhook:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))


class Guild:
    def __init__(self, error=None) -> None:
        self.events: list[dict] = []
        self.error = error

    async def create_scheduled_event(self, **kw):
        if self.error:
            raise self.error
        self.events.append(kw)
        return SimpleNamespace(url="https://discord.com/events/777/1")


class Chan:
    def __init__(self, id: int, guild=None) -> None:
        self.id = id
        self.guild = guild
        self.sent: list[tuple] = []
        self.msgs: dict[int, Msg] = {}
        self.webhook = Webhook()

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))

    def get_partial_message(self, id: int) -> Msg:
        return self.msgs.setdefault(id, Msg())

    async def create_webhook(self, *, name: str):
        return self.webhook


class Response:
    def __init__(self) -> None:
        self.sent: list[tuple] = []
        self.modal = None
        self.deferred = False

    async def send_message(self, content=None, **kw):
        self.sent.append((content, kw))

    async def send_modal(self, modal):
        self.modal = modal

    async def defer(self, **kw):
        self.deferred = True


def interaction(user_id: int):
    followup = SimpleNamespace(sent=[])

    async def send(content=None, **kw):
        followup.sent.append((content, kw))

    followup.send = send
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id), response=Response(), followup=followup
    )


def vote(user_id: int, answer_id: int):
    return SimpleNamespace(user_id=user_id, message_id=102, answer_id=answer_id)


@pytest.fixture
async def setup(store, fake_llm, monkeypatch):
    settings = Settings(discord_token="x", anthropic_api_key="x", gemini_api_key="x")
    bot = SquadBot(settings, store, fake_llm, None)
    vote_flow.setup(bot)
    guild = Guild()
    channel, thread = Chan(555, guild), Chan(900)
    monkeypatch.setattr(bot, "get_channel", {555: channel, 900: thread}.get)

    async def webhook_for(squad, ch):
        return ch.webhook

    monkeypatch.setattr(bot, "webhook_for", webhook_for)
    dms: list[tuple] = []

    async def dm(user_id, *, content=None, view=None):
        dms.append((user_id, view))
        return True

    bot.dm = dm
    yield SimpleNamespace(
        bot=bot, guild=guild, channel=channel, thread=thread, dms=dms, store=store
    )
    bot.flows.closer_loop.cancel()


async def seed(store, *members, votes=None) -> Plan:
    for m in members:
        await store.put_member(m)
    await store.put_squad(
        Squad(channel_id="555", guild_id="777", member_ids=[m.id for m in members])
    )
    plan = Plan(
        id="p1",
        channel_id="555",
        event=make_event(url="https://example.com/mic"),
        headline="Mic night",
        why="Both of you love music.",
        message_id="101",
        thread_id="900",
        poll_message_id="102",
        poll_closes_at=datetime.now(TZ) + timedelta(hours=1),
        status="polling",
        votes=votes or {},
        created_at=datetime.now(TZ),
    )
    await store.put_plan(plan)
    return plan


def card_lines(s) -> list[str]:
    return texts(s.channel.msgs[101].edits[-1]["view"])


async def test_vote_add_updates_card_and_dms_no_once(setup):
    s = setup
    await seed(s.store, make_member("1", name="Ash"), make_member("2", name="Sam"))
    await s.bot.on_raw_poll_vote_add(vote(1, 1))
    assert "✅ Ash" in card_lines(s)
    await s.bot.on_raw_poll_vote_add(vote(2, 3))
    await s.bot.on_raw_poll_vote_remove(vote(2, 3))
    await s.bot.on_raw_poll_vote_add(vote(2, 3))

    plan = s.store.plan("p1")
    assert plan.votes == {"1": "yes", "2": "no"}
    assert plan.why_no_asked == ["2"]
    assert [uid for uid, _ in s.dms] == ["2"]
    ids = [getattr(i, "custom_id", "") for i in s.dms[0][1].walk_children()]
    assert "squad:whyno:p1" in ids
    assert "❌ 1 can't make it" in card_lines(s)[-1]


async def test_vote_by_non_member_counts_no_dm(setup):
    s = setup
    await seed(s.store, make_member("1", name="Ash"))
    await s.bot.on_raw_poll_vote_add(vote(3, 3))
    assert s.store.plan("p1").votes == {"3": "no"}
    assert s.dms == []
    assert "❌ 1 can't make it" in card_lines(s)[-1]


async def test_vote_remove(setup):
    s = setup
    await seed(s.store, make_member("1", name="Ash"))
    await s.bot.on_raw_poll_vote_add(vote(1, 2))
    await s.bot.on_raw_poll_vote_remove(vote(1, 1))  # stale remove of another answer
    assert s.store.plan("p1").votes == {"1": "maybe"}
    await s.bot.on_raw_poll_vote_remove(vote(1, 2))
    assert s.store.plan("p1").votes == {}
    assert card_lines(s)[-1] == "Nobody's voted yet, no pressure 🙂"


async def test_persona_votes_and_jordan_learned_filter(setup, fake_llm, monkeypatch):
    s = setup
    monkeypatch.setattr(Settings, "persona_vote_delays_s", (0, 0, 0, 0))
    plan = await seed(s.store, make_member("1", name="Ash"), *PERSONAS)
    fake_llm.push(LearnedOut, LearnedOut(kind="no_weekday", value="4", keep=True))

    assert s.bot.flows.schedule_persona_votes(plan) is None  # never blocks run_plan
    await asyncio.gather(*s.bot.flows.schedule_persona_votes.__self__.tasks)

    assert s.store.plan("p1").votes == {
        "demo:maya": "yes",
        "demo:priya": "yes",
        "demo:leo": "maybe",
        "demo:jordan": "no",
    }
    posts = [(kw["username"], text) for text, kw in s.channel.webhook.sent]
    assert posts == [
        ("Maya", "count me in 🙌"),
        ("Priya", "count me in 🙌"),
        ("Leo", "probably! will confirm tonight"),
        ("Jordan", "can't this time 😔"),
        (
            "Jordan's agent",
            "Jordan shared why privately. I'll remember: no events after 9pm on Fridays.",
        ),
    ]
    assert all(kw["thread"].id == 900 for _, kw in s.channel.webhook.sent)
    (learned,) = s.store.member("demo:jordan").learned_filters
    assert (learned.kind, learned.value) == ("no_weekday", "4")
    assert "8am shift" not in " ".join(t for _, t in posts)
    assert s.dms == []


async def test_persona_no_without_filter_skips_agent_post(setup, monkeypatch):
    s = setup
    monkeypatch.setattr(Settings, "persona_vote_delays_s", (0, 0, 0, 0))
    plan = await seed(s.store, *PERSONAS)  # nothing queued: learn_from_no -> None
    s.bot.flows.schedule_persona_votes(plan)
    await asyncio.gather(*s.bot.flows.schedule_persona_votes.__self__.tasks)
    names = [kw["username"] for _, kw in s.channel.webhook.sent]
    assert "Jordan's agent" not in names
    assert s.store.member("demo:jordan").learned_filters == []


async def test_why_no_saves_filter_privately(setup, fake_llm):
    s = setup
    await seed(s.store, make_member("1", name="Ash"), votes={"1": "no"})
    fake_llm.push(LearnedOut, LearnedOut(kind="max_price", value="5", keep=True))
    click = interaction(1)
    await s.bot.flows.why_no(click, "p1")
    modal = click.response.modal
    assert modal.title == "Why not this time?"
    modal.reason._value = "too pricey for me rn"
    submit = interaction(1)
    await modal.on_submit(submit)

    (learned,) = s.store.member("1").learned_filters
    assert (learned.kind, learned.value) == ("max_price", "5")
    assert learned.source_text == "too pricey for me rn"
    assert fake_llm.calls[0]["effort"] == "low"
    assert submit.followup.sent == [
        ("Got it, I'll keep that in mind 🙏", {"ephemeral": True})
    ]
    assert s.channel.sent == [] and s.thread.sent == []
    assert s.channel.webhook.sent == []


async def test_why_no_one_off_thanks(setup, fake_llm):
    s = setup
    await seed(s.store, make_member("1", name="Ash"))
    fake_llm.push(LearnedOut, LearnedOut(kind="note", value="sick", keep=False))
    click = interaction(1)
    await s.bot.flows.why_no(click, "p1")
    click.response.modal.reason._value = "I'm sick"
    submit = interaction(1)
    await click.response.modal.on_submit(submit)
    assert s.store.member("1").learned_filters == []
    assert submit.followup.sent == [("Thanks for telling me 🙏", {"ephemeral": True})]


async def test_finish_creates_event_and_rides_once(setup):
    s = setup
    plan = await seed(
        s.store,
        make_member("1", name="Ash", seats=2),
        make_member("2", name="Sam"),
        make_member("3", name="Kai"),
        votes={"1": "yes", "2": "yes", "3": "no"},
    )
    await s.bot.flows.finish(plan)
    await s.bot.flows.finish(plan)

    (event,) = s.guild.events
    assert event["name"] == "Open Mic Night"
    assert event["start_time"] == plan.event.start
    assert event["end_time"] == plan.event.end
    assert event["entity_type"] == discord.EntityType.external
    assert event["privacy_level"] == discord.PrivacyLevel.guild_only
    assert event["location"] == plan.event.location
    assert event["description"] == "Both of you love music.\nhttps://example.com/mic"
    saved = s.store.plan("p1")
    assert saved.status == "closed"
    assert saved.discord_event_url == "https://discord.com/events/777/1"
    for target in (s.channel, s.thread):
        ((_, kw),) = target.sent
        lines = "\n".join(texts(kw["view"]))
        assert "**Going:** Ash, Sam" in lines
        assert "🚗 Ash → Sam" in lines
        assert "Discord event" in lines


async def test_finish_event_forbidden_still_posts_results(setup):
    s = setup
    s.guild.error = FORBIDDEN
    plan = await seed(s.store, make_member("1", name="Ash"), votes={"1": "yes"})
    await s.bot.flows.finish(plan)
    assert s.guild.events == []
    assert s.store.plan("p1").discord_event_url == ""
    for target in (s.channel, s.thread):
        ((_, kw),) = target.sent
        assert "**Going:** Ash" in texts(kw["view"])


async def test_nobody_going_message(setup):
    s = setup
    plan = await seed(s.store, make_member("1", name="Ash"), votes={"1": "maybe"})
    await s.bot.flows.finish(plan)
    msg = "Nobody could make it this time. Totally fine, there's always next week 🌙"
    assert s.channel.sent == [(msg, {})]
    assert s.thread.sent == [(msg, {})]
    assert s.guild.events == []
    assert s.store.plan("p1").status == "closed"


async def test_close_poll_members_only_then_finishes(setup):
    s = setup
    await seed(s.store, make_member("1", name="Ash"), votes={"1": "yes"})
    outsider = interaction(9)
    await s.bot.flows.close_poll(outsider, "p1")
    assert outsider.response.sent[0][1] == {"ephemeral": True}
    assert s.store.plan("p1").status == "polling"

    member = interaction(1)
    await s.bot.flows.close_poll(member, "p1")
    assert member.response.deferred
    assert s.channel.msgs[102].ended
    assert s.store.plan("p1").status == "closed"
    assert len(s.guild.events) == 1


async def test_close_due_finishes_only_expired_polls(setup):
    s = setup
    plan = await seed(s.store, make_member("1", name="Ash"), votes={"1": "yes"})
    flow = s.bot.flows.finish.__self__
    await flow.close_due(datetime.now(TZ))
    assert s.store.plan("p1").status == "polling"
    await flow.close_due(plan.poll_closes_at)
    assert s.store.plan("p1").status == "closed"

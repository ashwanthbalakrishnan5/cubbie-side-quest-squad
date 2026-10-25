from datetime import datetime
from types import SimpleNamespace

import discord
import pytest

from squad import demo_script
from squad.bot import SquadBot
from squad.config import Settings
from squad.flows import nudge_flow, plan_flow, vote_flow
from squad.personas import INTRO_LINES
from tests.fakes import TZ, make_member


class Msg:
    def __init__(self, id: int, channel=None) -> None:
        self.id = id
        self.channel = channel
        self.edits: list = []

    async def edit(self, **kw):
        self.edits.append(kw)

    async def create_thread(self, *, name: str):
        self.channel.thread_names.append(name)
        return SimpleNamespace(id=900)


class Webhook:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send(self, content=None, **kw):
        self.sent.append((kw["username"], content))


class Channel:
    id = 555
    name = "general"
    guild = SimpleNamespace(id=777)

    def __init__(self) -> None:
        self.sent: list[tuple] = []
        self.thread_names: list[str] = []
        self.webhook = Webhook()
        self.msgs: dict[int, Msg] = {}

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))
        return Msg(100 + len(self.sent), self)

    def get_partial_message(self, id: int) -> Msg:
        return self.msgs.setdefault(id, Msg(id))


class NoCalendar:
    def __getattr__(self, name):
        raise AssertionError(f"the demo must not touch the calendar ({name})")


def interaction(channel, user_id: int = 42):
    followup = SimpleNamespace(sent=[])

    async def send(content=None, **kw):
        followup.sent.append((content, kw))

    async def defer(**kw):
        pass

    followup.send = send
    user = SimpleNamespace(
        id=user_id,
        display_name="Ash",
        display_avatar=SimpleNamespace(url="https://cdn/ash.png"),
    )
    return SimpleNamespace(
        user=user,
        channel=channel,
        response=SimpleNamespace(defer=defer),
        followup=followup,
    )


@pytest.fixture
async def demo(store, fake_llm, monkeypatch):
    for name in dir(demo_script):
        if name.endswith("_S"):
            monkeypatch.setattr(demo_script, name, 0)

    async def no_feed(*a, **kw):
        raise AssertionError("the demo must not read the events feed")

    monkeypatch.setattr(plan_flow, "upcoming_events", no_feed)
    monkeypatch.setattr(nudge_flow, "in_quiet_hours", lambda *a: False)
    settings = Settings(
        discord_token="x",
        anthropic_api_key="x",
        gemini_api_key="x",
        wa_voice_url="",  # WhatsApp off: the presenter's nudge is a DM
        demo_phone="+14805550123",
    )
    bot = SquadBot(settings, store, fake_llm, NoCalendar())
    for flow in (plan_flow, vote_flow, nudge_flow):
        flow.setup(bot)
    channel = Channel()
    monkeypatch.setattr(bot, "get_channel", {555: channel}.get)

    async def webhook_for(squad, ch):
        return channel.webhook

    monkeypatch.setattr(bot, "webhook_for", webhook_for)
    dms: list[tuple] = []

    async def dm(user_id, *, content=None, view=None):
        dms.append((user_id, content))
        return True

    bot.dm = dm
    yield SimpleNamespace(bot=bot, channel=channel, dms=dms, llm=fake_llm)
    for loop in ("weekly_loop", "watch_loop", "closer_loop", "nudge_loop"):
        getattr(bot.flows, loop).cancel()


def texts(view) -> list[str]:
    return [
        i.content for i in view.walk_children() if isinstance(i, discord.ui.TextDisplay)
    ]


async def test_demo_runs_the_whole_script_without_claude_feed_or_calendar(demo, store):
    inter = interaction(demo.channel)
    await demo.bot.demo(inter)

    me = store.member("42")
    assert (me.name, me.budget_usd, me.seats, me.call_opt_in) == ("Ash", 20, 2, True)
    assert me.interests == ["music", "food", "chill"]
    assert me.phone == "+14805550123"
    assert "42" in store.squad("555").member_ids

    (intro, _), (_, card), (_, poll) = demo.channel.sent
    assert intro.startswith(
        "👀 Spotted something that fits everyone's week: **Open Mic Night**, <t:"
    )
    assert intro.endswith(":f>. Want to go?")
    card_texts = texts(card["view"])
    assert "_Live music, free pizza, and home by 9_" in card_texts
    assert any("Leo would've picked the hike" in t for t in card_texts)
    assert poll["poll"].question == "Open Mic Night, you in?"
    assert demo.channel.thread_names == ["🗺️ Open Mic Night"]

    (plan,) = store.plans()
    assert plan.status == "polling" and plan.thread_id == "900"
    assert plan.event.start.astimezone(TZ).weekday() == 4
    assert plan.event.start.astimezone(TZ).hour == 19
    assert plan.votes == {
        "demo:maya": "yes",
        "demo:priya": "yes",
        "demo:leo": "yes",
        "demo:jordan": "no",
    }
    posts = demo.channel.webhook.sent
    assert [text for _, text in posts[:4]] == list(INTRO_LINES.values())
    assert posts[4:] == [
        ("Maya's agent", "I'd love the open mic 🎤"),
        ("Jordan's agent", "happy to drive if it's not a late one"),
        ("Priya's agent", "free food and a chill crowd, yes"),
        ("Leo's agent", "I'd pick the hike, but I'm in for music"),
        ("Coordinator", demo_script.WHY),
        ("Priya's agent", "Priya's agent checked with Priya privately: all good."),
        ("Maya", "count me in 🙌"),
        ("Priya", "count me in 🙌"),
        ("Leo", "count me in 🙌"),
        ("Jordan", "can't this time 😔"),
        (
            "Jordan's agent",
            "Jordan shared why privately. I'll remember: no events after 9pm on Fridays.",
        ),
    ]
    (learned,) = store.member("demo:jordan").learned_filters
    assert learned.value == "no events after 9pm on Fridays"
    public = " ".join(t or "" for _, t in posts) + " ".join(card_texts)
    assert "8am shift" not in public and "cap" not in public

    assert demo.llm.calls == []
    # the presenter didn't vote, so they get nudged (a DM while WhatsApp is off)
    assert [uid for uid, _ in demo.dms] == ["42"]
    assert plan.nudged == ["42"]
    assert [text for text, _ in inter.followup.sent] == [
        demo_script.ROLLING,
        "💬 DMed Ash a nudge.",
    ]


async def test_demo_rerun_starts_fresh_plan_without_new_intros(demo, store):
    await store.put_member(make_member("42", name="Ash", budget_usd=0))
    for _ in range(2):
        await demo.bot.demo(interaction(demo.channel))

    first, second = store.plans()
    assert first.id != second.id
    names = [name for name, _ in demo.channel.webhook.sent]
    assert names.count("Maya") == 1 + 2  # one intro, one vote per run
    assert store.member("42").budget_usd == 0  # an existing member keeps their data
    assert store.squad("555").member_ids.count("42") == 1


async def test_demo_skips_the_nudge_once_the_presenter_voted(demo, store, monkeypatch):
    inter = interaction(demo.channel)
    real_vote = demo.bot.flows.persona_vote

    async def vote_then_presenter(plan, persona, vote):
        await real_vote(plan, persona, vote)
        plan.votes["42"] = "yes"

    monkeypatch.setattr(demo.bot.flows, "persona_vote", vote_then_presenter)
    await demo.bot.demo(inter)
    assert demo.dms == []
    assert [text for text, _ in inter.followup.sent] == [demo_script.ROLLING]


def test_demo_start_is_the_coming_friday_7pm():
    wed = datetime(2026, 10, 28, 12, tzinfo=TZ)
    fri_noon = datetime(2026, 10, 30, 12, tzinfo=TZ)
    fri_six = datetime(2026, 10, 30, 18, tzinfo=TZ)
    assert demo_script.demo_start(wed, TZ) == datetime(2026, 10, 30, 19, tzinfo=TZ)
    assert demo_script.demo_start(fri_noon, TZ) == datetime(2026, 10, 30, 19, tzinfo=TZ)
    assert demo_script.demo_start(fri_six, TZ) == datetime(2026, 11, 6, 19, tzinfo=TZ)

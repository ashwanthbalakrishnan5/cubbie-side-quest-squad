from datetime import datetime
from types import SimpleNamespace

import discord
import pytest

from squad import demo_script
from squad.bot import SquadBot, next_weekly_run
from squad.config import Settings
from squad.personas import INTRO_LINES, PERSONAS
from squad.ui.onboarding import CallsValues, JoinValues
from tests.fakes import TZ, make_member


@pytest.fixture(autouse=True)
def scripted_runs(monkeypatch) -> list:
    """No gaps, and the scripted run after the intros is recorded, not run (tests/test_demo.py runs it)."""
    for name in dir(demo_script):
        if name.endswith("_S"):
            monkeypatch.setattr(demo_script, name, 0)
    runs = []

    async def run(bot, interaction, squad):
        runs.append(squad.channel_id)

    monkeypatch.setattr(demo_script, "run", run)
    return runs


class Sink:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))


class Response:
    def __init__(self) -> None:
        self.sent: list[tuple] = []
        self.modal = None

    async def send_message(self, content=None, **kw):
        self.sent.append((content, kw))

    async def defer(self, **kw):
        pass

    async def send_modal(self, modal):
        self.modal = modal


class Webhook(Sink):
    url = "https://discord.com/api/webhooks/123/token"


class Channel:
    def __init__(self, id: int = 555) -> None:
        self.id = id
        self.guild = SimpleNamespace(id=777)
        self.webhooks_made: list[Webhook] = []

    async def create_webhook(self, *, name: str):
        assert name == "Squad Mode"
        self.webhooks_made.append(Webhook())
        return self.webhooks_made[-1]


class Calendar:
    def __init__(self) -> None:
        self.disconnected: list[str] = []

    def connect_url(self, member_id: str) -> str | None:
        return f"https://connect.example/{member_id}"

    def disconnect(self, member_id: str) -> None:
        self.disconnected.append(member_id)


def interaction(channel=None, user_id: int = 42):
    user = SimpleNamespace(
        id=user_id,
        display_name="Ash",
        display_avatar=SimpleNamespace(url="https://cdn/ash.png"),
    )
    return SimpleNamespace(
        user=user,
        channel=channel or Channel(),
        response=Response(),
        followup=Sink(),
    )


def make_bot(store, fake_llm, calendar=None) -> SquadBot:
    settings = Settings(discord_token="x", anthropic_api_key="x", gemini_api_key="x")
    return SquadBot(settings, store, fake_llm, calendar)


def texts_and_ids(view) -> tuple[list[str], list[str], list[str]]:
    items = list(view.walk_children())
    texts = [i.content for i in items if isinstance(i, discord.ui.TextDisplay)]
    ids = [getattr(i, "custom_id", None) for i in items]
    urls = [getattr(i, "url", None) for i in items]
    return texts, [i for i in ids if i], [u for u in urls if u]


JOIN = JoinValues(
    interests=["music", "food"],
    free_slots=["fri_night"],
    budget_key="10",
    no_go=["late"],
    seats_key="2",
)


async def test_join_submitted_creates_member_and_adds_to_squad(store, fake_llm):
    bot = make_bot(store, fake_llm, Calendar())
    inter = interaction()
    await bot.flows.join_submitted(inter, JOIN)

    member = store.member("42")
    assert member.name == "Ash" and member.budget_usd == 10 and member.seats == 2
    assert store.squad("555").member_ids == ["42"]
    assert store.squad("555").guild_id == "777"

    (_, kw), *_ = inter.followup.sent
    assert kw["ephemeral"] is True
    texts, ids, urls = texts_and_ids(kw["view"])
    assert texts[0] == "You're in 🎉 One more step:"
    assert texts[-1] == "No calendar? I'll use the free times you ticked."
    assert "squad:step2" in ids
    assert urls == ["https://connect.example/42"]

    await bot.flows.join_submitted(inter, JOIN)  # re-joining doesn't duplicate
    assert store.squad("555").member_ids == ["42"]


async def test_join_still_answers_when_calendar_link_fails(store, fake_llm):
    class Down(Calendar):
        def connect_url(self, member_id: str) -> str | None:
            raise RuntimeError("composio down")

    bot = make_bot(store, fake_llm, Down())
    inter = interaction()
    await bot.flows.join_submitted(inter, JOIN)
    texts, ids, urls = texts_and_ids(inter.followup.sent[0][1]["view"])
    assert texts[0] == "You're in 🎉 One more step:"
    assert "squad:step2" in ids and urls == []


async def test_join_without_calendar_has_no_link(store, fake_llm):
    bot = make_bot(store, fake_llm, None)
    inter = interaction()
    await bot.flows.join_submitted(inter, JOIN)
    _, _, urls = texts_and_ids(inter.followup.sent[0][1]["view"])
    assert urls == []


async def test_open_step2_sends_prefilled_calls_modal(store, fake_llm):
    await store.put_member(make_member("42", phone="+14805550123"))
    bot = make_bot(store, fake_llm)
    inter = interaction()
    await bot.flows.open_step2(inter)
    assert inter.response.modal.phone.default == "+14805550123"


async def test_calls_submitted_bad_phone_saves_nothing(store, fake_llm):
    await store.put_member(make_member("42"))
    bot = make_bot(store, fake_llm)
    inter = interaction()
    await bot.flows.calls_submitted(inter, CallsValues("call me maybe", True, "23-8"))

    member = store.member("42")
    assert member.phone == "" and member.quiet_hours == "22-9"
    assert inter.response.sent == [
        (
            "That number doesn't look right. Try something like +1 480 555 0123.",
            {"ephemeral": True},
        )
    ]

    inter = interaction()
    await bot.flows.calls_submitted(inter, CallsValues("480 555 0123", True, "23-8"))
    assert store.member("42").phone == "+14805550123"
    assert inter.response.sent == [("Saved ✨", {"ephemeral": True})]


async def test_leave_deletes_member_and_calendar(store, fake_llm):
    calendar = Calendar()
    bot = make_bot(store, fake_llm, calendar)
    inter = interaction()
    await bot.flows.join_submitted(inter, JOIN)

    inter = interaction()
    await bot.leave(inter)
    assert store.member("42") is None
    assert store.squad("555").member_ids == []
    assert calendar.disconnected == ["42"]
    assert inter.followup.sent == [
        (
            (
                "Done. I forgot everything about you (calendar link too). "
                "Come back anytime with /squad join."
            ),
            {"ephemeral": True},
        )
    ]


async def test_demo_adds_four_personas_once(store, fake_llm, scripted_runs):
    bot = make_bot(store, fake_llm)
    channel = Channel()
    for _ in range(2):
        inter = interaction(channel)
        await bot.demo(inter)
        assert inter.followup.sent == [(demo_script.ROLLING, {"ephemeral": True})]
    assert scripted_runs == ["555", "555"]

    ids = [p.id for p in PERSONAS]
    assert store.squad("555").member_ids == [*ids, "42"]
    assert [store.member(i).is_demo for i in ids] == [True] * 4
    assert len(channel.webhooks_made) == 1
    assert store.squad("555").webhook_url == Webhook.url
    sent = channel.webhooks_made[0].sent
    assert [text for text, _ in sent] == [INTRO_LINES[i.split(":")[1]] for i in ids]
    assert [kw["username"] for _, kw in sent] == ["Maya", "Jordan", "Priya", "Leo"]


NO_WEBHOOK = (
    "I can't bring demo friends in here. Try /squad demo in a server channel "
    "where I can manage webhooks 🙂"
)


async def test_demo_without_webhook_replies_softly_and_saves_no_ids(store, fake_llm):
    class NoPerm(Channel):
        async def create_webhook(self, *, name: str):
            raise discord.Forbidden(SimpleNamespace(status=403, reason="x"), "")

    bot = make_bot(store, fake_llm)
    for channel in (SimpleNamespace(id=999, guild=None), NoPerm(888)):  # DM, no perm
        for _ in range(2):  # a retry must not claim intros that never posted
            inter = interaction(channel)
            await bot.demo(inter)
            assert inter.followup.sent == [(NO_WEBHOOK, {"ephemeral": True})]
            assert store.squad(str(channel.id)).member_ids == []


async def test_demo_in_thread_posts_through_parent_webhook(store, fake_llm):
    text_channel = Channel()

    class Thread(discord.Thread):
        parent = text_channel  # shadows the cache-backed property

        def __init__(self) -> None:
            self.id = 556
            self.guild = text_channel.guild

    thread = Thread()
    bot = make_bot(store, fake_llm)
    inter = interaction(thread)
    await bot.demo(inter)
    assert len(text_channel.webhooks_made) == 1
    sent = text_channel.webhooks_made[0].sent
    assert [kw["thread"] for _, kw in sent] == [thread] * 4
    assert store.squad("556").member_ids == [*(p.id for p in PERSONAS), "42"]


async def test_dm_returns_false_on_forbidden(store, fake_llm, monkeypatch):
    bot = make_bot(store, fake_llm)
    forbidden = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "")

    class User:
        sent: list | None = None

        async def send(self, **kw):
            if self.sent is None:
                raise forbidden
            self.sent.append(kw)

    user = User()
    user.sent = []
    monkeypatch.setattr(bot, "get_user", lambda _id: user)
    assert await bot.dm("42", content="hi") is True
    assert user.sent == [{"content": "hi", "view": None}]
    user.sent = None
    assert await bot.dm("42", content="hi") is False
    assert await bot.dm("demo:maya", content="hi") is False


async def test_plan_without_plan_flow_says_warming_up(store, fake_llm):
    bot = make_bot(store, fake_llm)
    inter = interaction()
    await bot.plan_from_interaction(inter, "")
    assert inter.response.sent == [
        ("Planning is warming up, try again in a sec", {"ephemeral": True})
    ]


async def test_setup_hook_registers_commands(store, fake_llm, monkeypatch):
    bot = make_bot(store, fake_llm)

    async def no_sync(**_):
        return []

    monkeypatch.setattr(bot.tree, "sync", no_sync)
    await bot.setup_hook()
    names = {c.name for c in bot.tree.get_commands()}
    assert {"squad"} <= names
    menus = bot.tree.get_commands(type=discord.AppCommandType.message)
    assert [m.name for m in menus] == ["Plan this"]
    squad = bot.tree.get_command("squad")
    assert {c.name for c in squad.commands} == {
        "join",
        "leave",
        "demo",
        "nudge",
        "plan",
        "weekly",
    }


def test_next_weekly_run():
    wed_noon = datetime(2026, 10, 28, 12, 0, tzinfo=TZ)  # a Wednesday
    assert next_weekly_run(2, 18, wed_noon) == datetime(2026, 10, 28, 18, tzinfo=TZ)
    assert next_weekly_run(2, 9, wed_noon) == datetime(2026, 11, 4, 9, tzinfo=TZ)
    assert next_weekly_run(0, 8, wed_noon) == datetime(2026, 11, 2, 8, tzinfo=TZ)


DEMO_RETRY = "Couldn't bring everyone in just now. Try /squad demo again in a sec 🙂"


def http_error(cls, status: int):
    return cls(SimpleNamespace(status=status, reason="x"), "")


async def test_demo_failed_intro_retry_posts_only_missing(store, fake_llm, monkeypatch):
    class Flaky(Webhook):
        async def send(self, content=None, **kw):
            if len(self.sent) == 2 and not getattr(self, "failed", False):
                self.failed = True
                raise http_error(discord.HTTPException, 500)
            await super().send(content, **kw)

    class FlakyChannel(Channel):
        async def create_webhook(self, *, name: str):
            self.webhooks_made.append(Flaky())
            return self.webhooks_made[-1]

    bot = make_bot(store, fake_llm)
    channel = FlakyChannel()
    inter = interaction(channel)
    await bot.demo(inter)
    assert inter.followup.sent == [(DEMO_RETRY, {"ephemeral": True})]
    assert store.squad("555").member_ids == ["demo:maya", "demo:jordan"]

    hook = channel.webhooks_made[0]
    monkeypatch.setattr(discord.Webhook, "from_url", lambda url, client: hook)
    inter = interaction(channel)
    await bot.demo(inter)
    assert [kw["username"] for _, kw in hook.sent] == ["Maya", "Jordan", "Priya", "Leo"]
    assert store.squad("555").member_ids == [*(p.id for p in PERSONAS), "42"]


async def test_demo_stale_webhook_is_forgotten(store, fake_llm, monkeypatch):
    class Gone(Webhook):
        async def send(self, content=None, **kw):
            raise http_error(discord.NotFound, 404)

    monkeypatch.setattr(discord.Webhook, "from_url", lambda url, client: Gone())
    bot = make_bot(store, fake_llm)
    channel = Channel()
    squad = await bot.squad_for(channel)
    squad.webhook_url = "https://discord.com/api/webhooks/1/deleted"
    await store.put_squad(squad)

    inter = interaction(channel)
    await bot.demo(inter)
    assert inter.followup.sent == [(DEMO_RETRY, {"ephemeral": True})]
    assert store.squad("555").webhook_url == ""

    inter = interaction(channel)
    await bot.demo(inter)  # makes a fresh webhook
    assert len(channel.webhooks_made) == 1
    assert store.squad("555").member_ids == [*(p.id for p in PERSONAS), "42"]

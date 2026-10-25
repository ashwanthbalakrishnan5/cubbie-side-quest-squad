"""The scripted /squad demo for live table demos: the demo film's Open Mic Night, no Claude, feed or calendars."""

from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta
from hashlib import sha1
from typing import TYPE_CHECKING
from uuid import uuid4

import discord

from .constants import FREE_SLOTS
from .flows.plan_flow import SPOTTED_ALL
from .models import AgentTurn, Event, LearnedFilter, Member, Plan, Squad
from .personas import DEMO_VOTES

if TYPE_CHECKING:
    from .bot import SquadBot

# gaps in seconds; tests set every *_S to 0
INTRO_GAP_S = 1.5
STEP_GAP_S = 2.0
TURN_GAP_S = 1.2
VOTE_GAP_S = 2.5
NUDGE_AFTER_S = 8.0

TITLE = "Open Mic Night"
WHY = (
    "Maya and Leo both want music, Priya's in for the free food and a chill crowd, "
    "and it wraps up early enough for Jordan's Saturday."
)
TURNS = [
    ("maya", "I'd love the open mic 🎤"),
    ("jordan", "happy to drive if it's not a late one"),
    ("priya", "free food and a chill crowd, yes"),
    ("leo", "I'd pick the hike, but I'm in for music"),
]
PRIYA_CHECK = "Priya's agent checked with Priya privately: all good."
VOTES = [("maya", "yes"), ("priya", "yes"), ("leo", "yes"), ("jordan", "no")]
ROLLING = (
    "Demo's rolling 🎬 Vote in the poll when it lands (try Can't make it ❌ to see the "
    "private why), then hit Close poll now."
)


def demo_start(now: datetime, tz) -> datetime:
    """The coming Friday 7 PM; on a Friday after 5 PM, the next one."""
    local = now.astimezone(tz)
    days = (4 - local.weekday()) % 7
    if days == 0 and local.hour >= 17:
        days = 7
    return datetime.combine(local.date() + timedelta(days=days), time(19), tz)


def demo_plan(channel_id: str, now: datetime, tz) -> Plan:
    start = demo_start(now, tz)
    event = Event(
        id=sha1(f"{TITLE}{start.isoformat()}".encode()).hexdigest()[:10],
        title=TITLE,
        start=start,
        end=start + timedelta(hours=2),
        location="Memorial Union 202, Tempe Campus",
        description="Bring a song, a poem or just yourself. Free pizza.",
        tags=["music", "food"],
        free_food=True,
        price_usd=5.0,
    )
    turns = [
        AgentTurn(
            speaker=f"{key.capitalize()}'s agent", member_id=f"demo:{key}", text=t
        )
        for key, t in TURNS
    ]
    turns.append(AgentTurn(speaker="Coordinator", text=WHY))
    return Plan(
        id=uuid4().hex[:10],
        channel_id=channel_id,
        event=event,
        status="polling",
        headline="Live music, free pizza, and home by 9",
        why=WHY,
        tradeoffs=["Someone has a budget limit", "Leo would've picked the hike"],
        turns=turns,
        created_at=now,
    )


def presenter(user: discord.abc.User, phone: str) -> Member:
    """The person running /squad demo, signed up with the film's answers so nothing waits on the forms."""
    return Member(
        id=str(user.id),
        name=user.display_name,
        avatar_url=user.display_avatar.url,
        interests=["music", "food", "chill"],
        free_slots=list(FREE_SLOTS),
        budget_usd=20,
        seats=2,
        call_opt_in=True,
        phone=phone,
    )


async def run(bot: SquadBot, interaction: discord.Interaction, squad: Squad) -> None:
    """Watcher line, card, thread, poll and persona votes; the presenter votes and closes the poll live."""
    channel, tz, store = interaction.channel, bot.settings.tz, bot.store
    now = datetime.now(tz)
    squad.last_watch_post = now  # keeps the real watcher out of the demo for a while
    await store.put_squad(squad)
    plan = demo_plan(squad.channel_id, now, tz)
    unix = int(plan.event.start.timestamp())
    await channel.send(SPOTTED_ALL.format(title=TITLE, unix=unix))
    await asyncio.sleep(STEP_GAP_S)

    members = store.members(squad.member_ids)
    lines = [(store.member("demo:priya"), PRIYA_CHECK)]
    await bot.flows.post_plan(squad, channel, plan, members, lines, gap=TURN_GAP_S)

    for key, vote in VOTES:
        await asyncio.sleep(VOTE_GAP_S)
        if plan.status != "polling":
            return
        persona = store.member(f"demo:{key}")
        await bot.flows.persona_vote(plan, persona, vote)
        if key == "jordan":  # canned, so the demo never waits on Claude
            learned = LearnedFilter(
                kind="note",
                value="no events after 9pm on Fridays",
                source_text=DEMO_VOTES["jordan"][2],
                created_at=now,
            )
            await bot.flows.persona_learned(plan, persona, learned)

    await asyncio.sleep(NUDGE_AFTER_S)
    me = store.member(str(interaction.user.id))
    if plan.status == "polling" and me and me.id not in plan.votes:
        await interaction.followup.send(await bot.flows.ring(plan, me), ephemeral=True)

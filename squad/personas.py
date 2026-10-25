"""Four demo friends who make a solo demo feel like a real group chat."""

from __future__ import annotations

from datetime import datetime, time, timedelta

import discord
from discord.utils import MISSING

from squad.constants import FREE_SLOTS
from squad.models import BusyBlock, Member


def _persona(key: str, name: str, **fields) -> Member:
    return Member(
        id=f"demo:{key}",
        name=name,
        is_demo=True,
        avatar_url=f"https://api.dicebear.com/9.x/notionists/png?seed={name}&size=128",
        **fields,
    )


PERSONAS: list[Member] = [
    _persona(
        "maya",
        "Maya",
        interests=["music", "arts", "food"],
        free_slots=["fri_night", "sat_night", "sun_day"],
        budget_usd=20,
        no_go=["sports"],
        seats=0,
    ),
    _persona(
        "jordan",
        "Jordan",
        interests=["sports", "gaming", "food"],
        free_slots=["weeknights", "sat_day", "fri_night"],
        budget_usd=10,
        no_go=["late"],
        seats=3,
    ),
    _persona(
        "priya",
        "Priya",
        interests=["tech", "food", "chill"],
        free_slots=list(FREE_SLOTS),
        budget_usd=0,
        no_go=["parties", "alcohol"],
        seats=0,
    ),
    _persona(
        "leo",
        "Leo",
        interests=["outdoors", "chill", "music"],
        free_slots=["sat_day", "sat_night", "sun_day", "fri_night"],
        budget_usd=40,
        seats=1,
    ),
]

# member id -> (days after Monday, start hour, end hour)
_BUSY: dict[str, list[tuple[int, int, int]]] = {
    "demo:leo": [(3, 18, 21)],
    "demo:maya": [(5, 12, 16)],
}


CLASSES = [(d, 9, 16) for d in range(5)]  # everyone's in class Mon–Fri daytime


def persona_busy(member: Member, week_of: datetime, tz) -> list[BusyBlock]:
    """Class hours plus the persona's own blocks, for this week and next (plans look 7 days ahead)."""
    day = week_of.astimezone(tz).date()
    monday = day - timedelta(days=day.weekday())
    blocks = []
    for week in (0, 7):
        for offset, start_h, end_h in CLASSES + _BUSY.get(member.id, []):
            d = monday + timedelta(days=week + offset)
            blocks.append(
                BusyBlock(
                    start=datetime.combine(d, time(start_h), tz),
                    end=datetime.combine(d, time(end_h), tz),
                )
            )
    return blocks


INTRO_LINES: dict[str, str] = {
    "maya": "hii, Maya here 🎨 down for anything with music or art",
    "jordan": "Jordan. I'll drive if it's not a late one 🚗",
    "priya": "Priya! free stuff only pls, I'm a broke CS major 💻",
    "leo": "Leo 🌵 outdoorsy, will go anywhere with snacks",
}

DEMO_VOTES: dict[str, tuple[int, str, str | None]] = {
    "maya": (0, "yes", None),
    "priya": (1, "yes", None),
    "leo": (2, "maybe", None),
    "jordan": (
        3,
        "no",
        "I've got an 8am shift Saturday, nothing after 9 on Fridays for me",
    ),
}


async def post_as(
    webhook: discord.Webhook,
    name: str,
    avatar_url: str,
    text: str,
    thread: discord.abc.Snowflake | None = None,
) -> None:
    await webhook.send(
        text,
        username=name,
        avatar_url=avatar_url,
        thread=thread or MISSING,
        allowed_mentions=discord.AllowedMentions.none(),
    )

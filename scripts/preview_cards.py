"""Post plan, results and no-plan cards to the "🔧 dev previews" thread.

Usage: uv run python scripts/preview_cards.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import discord

from squad.config import load_settings
from squad.models import Car, Plan, Rides
from squad.ui.cards import no_plan_card, plan_card, results_card
from tests.fakes import TZ, make_event

THREAD = "🔧 dev previews"
NAMES = {"maya": "Maya", "jordan": "Jordan", "priya": "Priya", "leo": "Leo"}


def sample_plan() -> Plan:
    return Plan(
        id="preview",
        channel_id="0",
        event=make_event(url="https://sundevilcentral.eoss.asu.edu", free_food=True),
        headline="Open mic, free pizza, home by ten",
        why="Maya and Priya are into live music, and it fits everyone's Friday.",
        tradeoffs=["Starts a little early for Leo"],
        votes={"maya": "yes", "jordan": "maybe", "priya": "yes", "leo": "no"},
        discord_event_url="https://discord.com/events",
        created_at=datetime.now(TZ),
    )


async def post(client: discord.Client) -> None:
    channel = await client.fetch_channel(load_settings().dev_channel_id)
    thread = discord.utils.get(channel.threads, name=THREAD)
    if thread is None:
        async for t in channel.archived_threads(limit=50):
            if t.name == THREAD:
                thread = t
                break
    if thread is None:
        thread = await channel.create_thread(
            name=THREAD, type=discord.ChannelType.public_thread
        )
    plan = sample_plan()
    rides = Rides(
        cars=[Car(driver_id="maya", rider_ids=["priya"])],
        transit_ids=["jordan"],
        transit_tip="Valley Metro Rail to Veterans Way/College Ave, 5 min walk.",
    )
    reason = "Nothing this week fit everyone, so I'm not forcing it."
    for view in (
        plan_card(plan, NAMES, TZ),
        results_card(plan, NAMES, rides, TZ),
        no_plan_card(reason, plan.event, TZ),
    ):
        await thread.send(view=view)
    print(f"Posted 3 cards to thread {thread.id}")


def main() -> None:
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready() -> None:
        try:
            await post(client)
        finally:
            await client.close()

    client.run(load_settings().discord_token, log_handler=None)


if __name__ == "__main__":
    main()

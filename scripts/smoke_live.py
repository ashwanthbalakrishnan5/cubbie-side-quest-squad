"""Live end-to-end check against the real Discord test server.

Logs in as the bot (stop any running `python -m squad` first: one token, one session), brings in the demo squad,
plans a real side quest in DEV_CHANNEL_ID, waits for the persona votes, closes the poll and checks the results
through Discord's REST API. Uses a separate store under data/smoke/.

    DEMO_FAST=1 uv run python scripts/smoke_live.py
"""

from __future__ import annotations

import asyncio
import dataclasses
import sys
from pathlib import Path

import aiohttp
from anthropic import AsyncAnthropic
from composio import Composio

from squad.bot import SquadBot
from squad.calendar import CalendarLinker
from squad.config import load_settings
from squad.llm import LLM
from squad.models import Request
from squad.store import Store

API = "https://discord.com/api/v10"
COMPONENTS_V2 = 1 << 15


class _Followup:
    async def send(self, *args, **kwargs):
        print("  (ephemeral)", kwargs.get("content") or args[:1] or "view")


class _Response:
    async def defer(self, **kwargs):
        pass

    async def send_message(self, *args, **kwargs):
        print("  (ephemeral)", kwargs.get("content") or args[:1] or "view")


class FakeInteraction:
    """Just enough of discord.Interaction for SquadBot.demo."""

    def __init__(self, channel, user):
        self.channel, self.user = channel, user
        self.response, self.followup = _Response(), _Followup()


async def rest(session: aiohttp.ClientSession, path: str):
    async with session.get(API + path) as resp:
        resp.raise_for_status()
        return await resp.json()


async def main() -> int:
    settings = dataclasses.replace(
        load_settings(), demo_fast=True, data_dir=Path("data/smoke")
    )
    calendar = (
        CalendarLinker(
            Composio(api_key=settings.composio_api_key),
            settings.composio_calendar_auth_config,
            f"{settings.public_url}/calendar/done",
        )
        if settings.composio_api_key
        else None
    )
    bot = SquadBot(
        settings,
        Store(settings.data_dir / "squad.json"),
        LLM(AsyncAnthropic(api_key=settings.anthropic_api_key)),
        calendar,
    )
    await bot.login(settings.discord_token)
    runner = asyncio.create_task(bot.connect())
    failures: list[str] = []
    try:
        await asyncio.wait_for(bot.wait_until_ready(), 60)
        channel = bot.get_channel(settings.dev_channel_id) or await bot.fetch_channel(
            settings.dev_channel_id
        )
        print(f"ready as {bot.user}; channel #{channel.name}")

        await bot.demo(FakeInteraction(channel, bot.user))
        squad = await bot.squad_for(channel)
        print(f"squad members: {squad.member_ids}")

        print("planning (real feed + Claude)…")
        await bot.flows.run_plan(squad, channel, Request())
        plans = [p for p in bot.store.plans("polling") if p.channel_id == str(channel.id)]
        if not plans:
            print("no plan posted (see channel for the no-plan card)")
            return 1
        plan = max(plans, key=lambda p: p.created_at)
        print(f"plan {plan.id}: {plan.event.title} @ {plan.event.start}")

        await asyncio.sleep(max(settings.persona_vote_delays_s) + 8)
        plan = bot.store.plan(plan.id)
        print(f"votes after personas: {plan.votes}")
        await bot.flows.finish(plan)
        plan = bot.store.plan(plan.id)

        headers = {"Authorization": f"Bot {settings.discord_token}"}
        async with aiohttp.ClientSession(headers=headers) as s:
            card = await rest(s, f"/channels/{channel.id}/messages/{plan.message_id}")
            poll = await rest(s, f"/channels/{channel.id}/messages/{plan.poll_message_id}")
            thread_msgs = await rest(s, f"/channels/{plan.thread_id}/messages?limit=50")
            events = await rest(s, f"/guilds/{channel.guild.id}/scheduled-events")
        if not card["flags"] & COMPONENTS_V2:
            failures.append("plan card is not a components-v2 message")
        if len(poll.get("poll", {}).get("answers", [])) != 3:
            failures.append("poll does not have 3 answers")
        webhook_posts = [m for m in thread_msgs if m.get("webhook_id")]
        if len(webhook_posts) < 4:
            failures.append(f"thread has {len(webhook_posts)} webhook posts, want >= 4")
        if plan.status != "closed":
            failures.append(f"plan status is {plan.status}, want closed")
        if not any(e["name"] == plan.event.title[:100] for e in events):
            failures.append("no Discord scheduled event for the plan")
        if not plan.votes:
            failures.append("no votes recorded")

        base = f"https://discord.com/channels/{channel.guild.id}"
        print(f"card:   {base}/{channel.id}/{plan.message_id}")
        print(f"poll:   {base}/{channel.id}/{plan.poll_message_id}")
        print(f"thread: {base}/{plan.thread_id}")
        print(f"event:  {plan.discord_event_url}")
    finally:
        await bot.close()
        runner.cancel()
    print("FAIL:\n- " + "\n- ".join(failures) if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

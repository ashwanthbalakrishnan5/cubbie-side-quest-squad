"""Live check of the scripted /squad demo against the real Discord test server.

Stop the hosted bot first (one token, one session): `ssh openclaw sudo systemctl stop squad`.
Runs the same code path as /squad demo in DEV_CHANNEL_ID with a separate store under data/smoke-demo/,
then presses "Close poll now" in code and checks the results through Discord's REST API.

    PYTHONPATH=. uv run python scripts/smoke_demo.py
"""

from __future__ import annotations

import asyncio
import dataclasses
import sys
from pathlib import Path

import aiohttp
from anthropic import AsyncAnthropic

from squad.bot import SquadBot
from squad.config import load_settings
from squad.llm import LLM
from squad.store import Store

API = "https://discord.com/api/v10"


class _Followup:
    async def send(self, *args, **kwargs):
        print("  (ephemeral)", kwargs.get("content") or (args[:1] or ["view"])[0])


class _Response:
    async def defer(self, **kwargs):
        pass

    async def send_message(self, *args, **kwargs):
        print("  (ephemeral)", kwargs.get("content") or (args[:1] or ["view"])[0])


class FakeInteraction:
    """Just enough of discord.Interaction for SquadBot.demo."""

    def __init__(self, channel, user):
        self.channel, self.user = channel, user
        self.response, self.followup = _Response(), _Followup()


async def main() -> int:
    settings = dataclasses.replace(load_settings(), data_dir=Path("data/smoke-demo"))
    bot = SquadBot(
        settings,
        Store(settings.data_dir / "squad.json"),
        LLM(AsyncAnthropic(api_key=settings.anthropic_api_key)),
        None,
    )
    await bot.login(settings.discord_token)
    runner = asyncio.create_task(bot.connect())
    failures: list[str] = []
    try:
        await asyncio.wait_for(bot.wait_until_ready(), 60)
        channel = bot.get_channel(settings.dev_channel_id) or await bot.fetch_channel(
            settings.dev_channel_id
        )
        print(f"ready as {bot.user}; channel #{channel.name}; running /squad demo…")
        started = asyncio.get_running_loop().time()
        await bot.demo(FakeInteraction(channel, bot.user))
        took = asyncio.get_running_loop().time() - started
        plans = [
            p for p in bot.store.plans("polling") if p.channel_id == str(channel.id)
        ]
        if not plans:
            print("FAIL: no polling plan after the demo")
            return 1
        plan = max(plans, key=lambda p: p.created_at)
        print(f"demo done in {took:.1f}s; plan {plan.id}: votes {plan.votes}")
        await bot.flows.finish(plan)
        plan = bot.store.plan(plan.id)

        headers = {"Authorization": f"Bot {settings.discord_token}"}
        async with aiohttp.ClientSession(headers=headers) as s:

            async def get(path):
                async with s.get(API + path) as r:
                    r.raise_for_status()
                    return await r.json()

            recent = await get(f"/channels/{channel.id}/messages?limit=15")
            thread = await get(f"/channels/{plan.thread_id}/messages?limit=50")
            events = await get(f"/guilds/{channel.guild.id}/scheduled-events")
        texts = [m.get("content", "") for m in recent]
        if not any("Spotted something" in t for t in texts):
            failures.append("no watcher line in the channel")
        if not any(m.get("poll") for m in recent):
            failures.append("no poll in the channel")
        if len([m for m in thread if m.get("webhook_id")]) < 6:
            failures.append("thread has fewer than 6 agent/persona posts")
        if {k for k, v in plan.votes.items() if k.startswith("demo:")} != {
            "demo:maya",
            "demo:priya",
            "demo:leo",
            "demo:jordan",
        }:
            failures.append(f"persona votes incomplete: {plan.votes}")
        if plan.status != "closed":
            failures.append(f"plan status {plan.status}, want closed")
        if not any(e["name"].startswith("Open Mic Night") for e in events):
            failures.append("no Discord scheduled event")
        if took > 60:
            failures.append(f"demo took {took:.0f}s, want under 60")
        base = f"https://discord.com/channels/{channel.guild.id}"
        print(f"card:   {base}/{channel.id}/{plan.message_id}")
        print(f"thread: {base}/{plan.thread_id}")
        print(f"event:  {plan.discord_event_url}")
    finally:
        await bot.close()
        runner.cancel()
    print("FAIL:\n- " + "\n- ".join(failures) if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

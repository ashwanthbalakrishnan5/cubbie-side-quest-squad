"""Nudge flow: a WhatsApp call (when paired) or a DM for members who haven't voted yet."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp
from discord.ext import tasks

from ..availability import in_quiet_hours
from ..config import Settings
from ..models import Member, Plan
from ..ui.cards import plan_card
from ..voice.bridge import nudge_call

if TYPE_CHECKING:
    from ..bot import SquadBot

log = logging.getLogger(__name__)


async def voice_connected(settings: Settings) -> bool:
    """True only when the wa-voice sidecar answers GET /status with connected."""
    if not settings.wa_voice_url:
        return False
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        async with (
            aiohttp.ClientSession(timeout=timeout) as http,
            http.get(f"{settings.wa_voice_url}/status") as r,
        ):
            return r.status == 200 and (await r.json()).get("connected") is True
    except Exception as e:  # noqa: BLE001 - an unreachable sidecar just means DMs
        log.info("wa-voice status unavailable: %s", type(e).__name__)
        return False


class NudgeFlow:
    def __init__(self, bot: SquadBot) -> None:
        self.bot = bot

    def nudge_due(self, plan: Plan, now: datetime) -> list[Member]:
        bot = self.bot
        squad = bot.store.squad(plan.channel_id)
        wait = timedelta(seconds=bot.settings.nudge_after_s)
        if plan.status != "polling" or squad is None or now < plan.created_at + wait:
            return []
        return [
            m
            for m in bot.store.members(squad.member_ids)
            if m.id not in plan.votes
            and m.id not in plan.nudged
            and not m.is_demo
            and not in_quiet_hours(m, now, bot.settings.tz)
        ]

    async def tick(self, now: datetime) -> None:
        store = self.bot.store
        for plan in store.plans("polling"):
            due = self.nudge_due(plan, now)
            if not due:
                continue
            plan.nudged += [m.id for m in due]
            await store.put_plan(plan)  # saved first, so each member is nudged once
            for member in due:
                try:
                    await self.nudge(plan, member)
                # one failed nudge must not stop the loop or the other nudges
                except Exception:
                    log.exception("nudge failed")

    async def _channel(self, channel_id: str):
        cid = int(channel_id)
        return self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)

    async def nudge(self, plan: Plan, member: Member) -> None:
        bot = self.bot
        settings = bot.settings
        if plan.status != "polling":  # closed while an earlier member was on a call
            return
        if member.call_opt_in and member.phone and await voice_connected(settings):
            members = bot.store.members(bot.store.squad(plan.channel_id).member_ids)
            names = {m.id: m.name for m in members}
            going = [
                names[u] for u, v in plan.votes.items() if v == "yes" and u in names
            ]
            outcome = await nudge_call(settings, member.phone, member.name, plan, going)
            if plan.status != "polling":  # poll closed mid-call: no vote, no DM
                return
            if outcome.answered and outcome.answer:
                plan.votes[member.id] = outcome.answer
                await bot.store.put_plan(plan)
                channel = await self._channel(plan.channel_id)
                card = channel.get_partial_message(int(plan.message_id))
                await card.edit(view=plan_card(plan, names, settings.tz))
                thread = await self._channel(plan.thread_id)
                # the reason stays private: only the answer is posted
                await thread.send(
                    f"📞 {member.name} picked up and said {outcome.answer}"
                )
                return
        channel = await self._channel(plan.channel_id)
        unix = int(plan.event.start.timestamp())
        text = (
            f"Hey {member.name} 👋 the squad's planning {plan.event.title} "
            f"<t:{unix}:R>. You in? The poll's in #{channel.name}."
        )
        if not await bot.dm(member.id, content=text):
            await channel.send(f"<@{member.id}> psst, there's a poll waiting for you 🗺️")


def setup(bot: SquadBot) -> None:
    flow = NudgeFlow(bot)
    bot.flows.nudge_due = flow.nudge_due
    bot.flows.nudge_tick = flow.tick

    @tasks.loop(seconds=30)
    async def nudge_loop() -> None:
        if bot.is_ready():  # channels aren't cached before ready
            await flow.tick(datetime.now(bot.settings.tz))

    bot.flows.nudge_loop = nudge_loop
    nudge_loop.start()

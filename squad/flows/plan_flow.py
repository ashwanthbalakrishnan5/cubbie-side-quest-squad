"""Plan flow: manual and weekly triggers, private confirmations, the card, its thread and the poll."""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import discord
from discord import ui
from discord.ext import tasks

from ..agents import parse_request
from ..constants import MAX_ROUNDS, VOTE_ANSWERS
from ..constraints import violations_for
from ..events import EventsUnavailable, upcoming_events
from ..models import BusyBlock, Event, Member, NoPlan, Plan, Request, Squad
from ..personas import persona_busy, post_as
from ..planner import build_plan, find_match
from ..ui.cards import _view, confirm_view, no_plan_card, plan_card

if TYPE_CHECKING:
    from ..bot import SquadBot

log = logging.getLogger(__name__)

ON_IT = "On it 🗺️ checking Sun Devil Central and everyone's week…"
FEED_DOWN = "Sun Devil Central isn't answering right now. I'll try again in a bit 🌵"
ALL_DECLINED = "I couldn't land on one that works for everyone this time."
NOTED = "Got it, thanks 🙏"
STALE = "That check already closed, thanks though 🙂"
GONE = "I can't find that plan anymore 🙂"
SPOTTED_ALL = "👀 Spotted something that fits everyone's week: **{title}**, <t:{unix}:f>. Want to go?"
SPOTTED_SOME = (
    "👀 {mentions}: **{title}**, <t:{unix}:f> fits your calendars and looks very you. "
    "Want to go? Anyone else is welcome too."
)
WATCH_HOURS = range(9, 22)  # the watcher never posts 22:00-09:00 local


class PlanFlow:
    def __init__(self, bot: SquadBot) -> None:
        self.bot = bot
        self.waiting: dict[tuple[str, str], asyncio.Future[bool]] = {}
        self.tasks: set[asyncio.Task] = set()  # strong refs for weekly runs

    async def plan_requested(self, message: discord.Message, text: str) -> None:
        await message.reply(ON_IT)
        await self._manual(message.channel, text)

    async def plan_requested_from_interaction(
        self, interaction: discord.Interaction, text: str
    ) -> None:
        await interaction.response.send_message(ON_IT)
        await self._manual(interaction.channel, text)

    async def _manual(self, channel, text: str) -> None:
        squad = await self.bot.squad_for(channel)
        now = datetime.now(self.bot.settings.tz)
        # an empty ask has nothing to parse, so skip the model call
        request = (
            await parse_request(self.bot.llm, text, now) if text.strip() else Request()
        )
        await self.run_plan(squad, channel, request)

    async def _busy(self, member: Member, now: datetime) -> list[BusyBlock] | None:
        tz = self.bot.settings.tz
        if member.is_demo:
            return persona_busy(member, now, tz)
        if self.bot.calendar is None:
            return None
        return await asyncio.to_thread(
            self.bot.calendar.busy_blocks, member.id, now, now + timedelta(days=7), tz
        )

    async def _busy_all(
        self, members: list[Member], now: datetime
    ) -> dict[str, list[BusyBlock] | None]:
        found = await asyncio.gather(*(self._busy(m, now) for m in members))
        return {m.id: b for m, b in zip(members, found)}

    async def run_plan(
        self,
        squad: Squad,
        channel,
        request: Request,
        intro: str | None = None,
        only_event: Event | None = None,
        members: list[Member] | None = None,
    ) -> None:
        bot, tz = self.bot, self.bot.settings.tz
        now = datetime.now(tz)
        if intro:
            await channel.send(
                intro,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, users=True, roles=False, replied_user=False
                ),
            )
        if only_event:
            # the watcher already read the feed; same as excluding every other event
            events = [only_event]
        else:
            try:
                events = await upcoming_events(bot.settings, now)
            except EventsUnavailable:
                await channel.send(FEED_DOWN)
                return
        members = members or bot.store.members(squad.member_ids)
        busy = await self._busy_all(members, now)

        async def build(exclude: set[str]) -> Plan | NoPlan:
            return await build_plan(
                members=members,
                events=events,
                busy=busy,
                request=request,
                llm=bot.llm,
                now=now,
                channel_id=squad.channel_id,
                tz=tz,
                exclude=exclude,
            )

        declined: list[str] = []
        lines: list[tuple[Member, str]] = []
        near_miss = None
        plan = await build(set())
        while isinstance(plan, Plan) and plan.ask_first:
            if await self._confirm(plan, members, busy, lines):
                break
            declined.append(plan.event.id)
            near_miss = plan.event
            if len(declined) >= MAX_ROUNDS:
                plan = NoPlan(reason=ALL_DECLINED)
            else:
                plan = await build(set(declined))
        if isinstance(plan, NoPlan):
            await channel.send(
                view=no_plan_card(plan.reason, plan.near_miss or near_miss, tz)
            )
            return
        plan.declined_event_ids = declined
        await self.post_plan(squad, channel, plan, members, lines)
        schedule = getattr(bot.flows, "schedule_persona_votes", None)
        if schedule:
            result = schedule(plan)
            if inspect.isawaitable(result):
                await result

    async def post_plan(
        self,
        squad: Squad,
        channel,
        plan: Plan,
        members: list[Member],
        lines: list[tuple[Member, str]],
        gap: float = 0,
    ) -> None:
        """Card, poll and thread for a ready plan; `gap` seconds between thread posts."""
        bot, tz = self.bot, self.bot.settings.tz
        names = {m.id: m.name for m in members}
        card = await channel.send(view=plan_card(plan, names, tz))
        poll = discord.Poll(
            question=f"{plan.event.title[:250]}, you in?",
            duration=timedelta(hours=squad.poll_hours),
        )
        for answer in VOTE_ANSWERS:
            poll.add_answer(text=answer)
        poll_message = await channel.send(poll=poll)
        thread = await card.create_thread(name=f"🗺️ {plan.event.title[:80]}")
        plan.message_id = str(card.id)
        plan.thread_id = str(thread.id)
        plan.poll_message_id = str(poll_message.id)
        plan.poll_closes_at = datetime.now(tz) + timedelta(hours=squad.poll_hours)
        plan.status = "polling"
        await bot.store.put_plan(plan)  # saved before the thread so early votes land

        await self._post_thread(squad, channel, thread, plan, members, lines, gap)

    async def _confirm(
        self,
        plan: Plan,
        members: list[Member],
        busy: dict[str, list[BusyBlock] | None],
        lines: list[tuple[Member, str]],
    ) -> bool:
        tz = self.bot.settings.tz
        asked = [m for m in members if m.id in plan.ask_first]
        humans = [m for m in asked if not m.is_demo]
        for m in asked:
            if m.is_demo:
                kinds = {v.kind for v in violations_for(m, plan.event, busy[m.id], tz)}
                yes = not kinds & {"late", "no_go"}
                plan.confirmations[m.id] = yes
                answer = "all good" if yes else "not this one"
                lines.append(
                    (m, f"{m.name}'s agent checked with {m.name} privately: {answer}.")
                )
        if not all(plan.confirmations.values()):
            return False  # a persona already said no; don't bother the humans

        unix = int(plan.event.start.timestamp())
        waits: dict[str, asyncio.Future[bool]] = {}
        for m in humans:
            details = violations_for(m, plan.event, busy.get(m.id), tz)
            heads_up = "; ".join(v.detail_private for v in details)
            text = (
                "Quick check before I post this week's plan: "
                f"{plan.event.title}, <t:{unix}:F>. Heads up: {heads_up}. "
                "Still up for it?"
            )
            future = asyncio.get_running_loop().create_future()
            self.waiting[(plan.id, m.id)] = (
                future  # before the DM, so a fast click lands
            )
            waits[m.id] = future
            if not await self.bot.dm(m.id, view=confirm_view(plan.id, text)):
                future.set_result(False)
        if waits:
            await asyncio.wait(
                waits.values(), timeout=self.bot.settings.confirm_timeout_s
            )
        for uid, future in waits.items():
            self.waiting.pop((plan.id, uid), None)
            plan.confirmations[uid] = future.done() and future.result()
        return all(plan.confirmations.get(uid, False) for uid in plan.ask_first)

    async def _post_thread(
        self,
        squad: Squad,
        channel,
        thread,
        plan: Plan,
        members: list[Member],
        lines: list[tuple[Member, str]],
        gap: float = 0,
    ) -> None:
        bot = self.bot
        avatars = {m.id: m.avatar_url for m in members}
        bot_avatar = bot.user.display_avatar.url if bot.user else ""
        posts = [
            (t.speaker, avatars.get(t.member_id, bot_avatar), t.text)
            for t in plan.turns
        ]
        posts += [(f"{m.name}'s agent", m.avatar_url, text) for m, text in lines]
        done = 0
        try:
            webhook = await bot.webhook_for(squad, channel)
            for name, avatar, text in posts:
                if gap:
                    await asyncio.sleep(gap)
                await post_as(webhook, name, avatar, text, thread=thread)
                done += 1
        # no Manage Webhooks or a deleted webhook: the bot posts the rest itself
        except (AttributeError, discord.HTTPException) as error:
            log.info("thread posts via webhook failed: %s", type(error).__name__)
            for name, _, text in posts[done:]:
                await thread.send(
                    f"**{name}:** {text}",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

    async def confirm(
        self, interaction: discord.Interaction, plan_id: str, answer: str
    ) -> None:
        future = self.waiting.get((plan_id, str(interaction.user.id)))
        if future is None or future.done():
            await interaction.response.send_message(STALE, ephemeral=True)
            return
        future.set_result(answer == "yes")
        await interaction.response.edit_message(view=_view(ui.TextDisplay(NOTED)))

    async def explain(self, interaction: discord.Interaction, plan_id: str) -> None:
        plan = self.bot.store.plan(plan_id)
        if plan is None:
            await interaction.response.send_message(GONE, ephemeral=True)
            return
        said = [f"**{t.speaker}:** {t.text}" for t in plan.turns if t.member_id]
        text = plan.why
        if said:
            text += "\n\n**What each agent said**\n" + "\n".join(said)
        await interaction.response.send_message(text[:2000], ephemeral=True)

    async def weekly_tick(self, now: datetime) -> None:
        local = now.astimezone(self.bot.settings.tz)
        for squad in self.bot.store.squads():
            due = (squad.weekly_weekday, squad.weekly_hour) == (
                local.weekday(),
                local.hour,
            )
            if not due or squad.last_weekly_date == local.date():
                continue
            channel = self.bot.get_channel(int(squad.channel_id))
            if channel is None or not squad.member_ids:
                continue
            squad.last_weekly_date = local.date()
            await self.bot.store.put_squad(squad)
            # one task per squad so a 10-minute confirmation wait never blocks the loop
            task = asyncio.create_task(self._weekly_run(squad, channel))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

    async def watch_tick(self, now: datetime) -> None:
        bot = self.bot
        if now.astimezone(bot.settings.tz).hour not in WATCH_HOURS:
            return
        gap = timedelta(minutes=10) if bot.settings.demo_fast else timedelta(hours=72)
        busy_channels = {p.channel_id for p in bot.store.plans("confirming", "polling")}
        for squad in bot.store.squads():
            if len(squad.member_ids) < 2 or squad.channel_id in busy_channels:
                continue
            if squad.last_watch_post and now - squad.last_watch_post < gap:
                continue
            channel = bot.get_channel(int(squad.channel_id))
            if channel is None:
                continue
            try:
                await self._watch(squad, channel, now)
            except Exception:  # one squad's failure must not stop the loop
                log.exception("watcher failed for a squad")

    async def _watch(self, squad: Squad, channel, now: datetime) -> None:
        bot = self.bot
        try:
            events = await upcoming_events(bot.settings, now)
        except EventsUnavailable:
            return  # nobody asked, so a feed outage stays quiet
        members = bot.store.members(squad.member_ids)
        busy = await self._busy_all(members, now)
        match = find_match(
            members, events, busy, bot.settings.tz, now, set(squad.suggested_event_ids)
        )
        if match is None:
            return
        event, who = match
        squad.suggested_event_ids.append(event.id)
        squad.last_watch_post = now
        await bot.store.put_squad(squad)
        unix = int(event.start.timestamp())
        if len(who) == len(members):
            intro = SPOTTED_ALL.format(title=event.title, unix=unix)
        else:
            mentions = ", ".join(m.name if m.is_demo else f"<@{m.id}>" for m in who)
            intro = SPOTTED_SOME.format(mentions=mentions, title=event.title, unix=unix)
        await bot.flows.run_plan(
            squad, channel, Request(), intro=intro, only_event=event, members=who
        )

    async def _weekly_run(self, squad: Squad, channel) -> None:
        try:
            await channel.send(ON_IT)
            await self.bot.flows.run_plan(squad, channel, Request())
        except Exception:
            log.exception("weekly plan failed for a squad")


def setup(bot: SquadBot) -> None:
    flow = PlanFlow(bot)
    flows = bot.flows
    flows.plan_requested = flow.plan_requested
    flows.plan_requested_from_interaction = flow.plan_requested_from_interaction
    flows.confirm = flow.confirm
    flows.explain = flow.explain
    flows.run_plan = flow.run_plan
    flows.post_plan = flow.post_plan
    flows.weekly_tick = flow.weekly_tick
    flows.watch_tick = flow.watch_tick

    @tasks.loop(minutes=1)
    async def weekly_loop() -> None:
        if bot.is_ready():  # channels aren't cached before ready
            await flow.weekly_tick(datetime.now(bot.settings.tz))

    flows.weekly_loop = weekly_loop
    weekly_loop.start()

    @tasks.loop(minutes=2 if bot.settings.demo_fast else 180)
    async def watch_loop() -> None:
        if bot.is_ready():
            await flow.watch_tick(datetime.now(bot.settings.tz))

    flows.watch_loop = watch_loop
    watch_loop.start()

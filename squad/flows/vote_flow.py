"""Vote flow: poll votes, demo persona votes, the private "why no?", closing, rides and the Discord event."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord import ui
from discord.ext import tasks

from ..agents import learn_from_no
from ..carpool import plan_rides
from ..constants import VOTE_KEYS
from ..models import LearnedFilter, Member, Plan
from ..personas import DEMO_VOTES, post_as
from ..ui.cards import plan_card, results_card, why_no_view

if TYPE_CHECKING:
    from ..bot import SquadBot

log = logging.getLogger(__name__)

PERSONA_LINES = {
    "yes": "count me in 🙌",
    "maybe": "probably! will confirm tonight",
    "no": "can't this time 😔",
}
JORDAN_LEARNED = (
    "Jordan shared why privately. I'll remember: no events after 9pm on Fridays."
)
NOBODY = "Nobody could make it this time. Totally fine, there's always next week 🌙"
KEPT = "Got it, I'll keep that in mind 🙏"
THANKS = "Thanks for telling me 🙏"
MEMBERS_ONLY = "Only folks in this squad can close the poll 🙂"
ALREADY_CLOSED = "That poll's already closed 🙂"
GONE = "I can't find that plan anymore 🙂"


class WhyNoModal(ui.Modal, title="Why not this time?"):
    def __init__(self, vote_flow: VoteFlow, plan_id: str) -> None:
        super().__init__()
        self.vote_flow = vote_flow
        self.plan_id = plan_id
        self.reason = ui.TextInput(
            style=discord.TextStyle.paragraph, required=False, max_length=300
        )
        self.add_item(
            ui.Label(
                text="What got in the way?",
                description="Only I see this",
                component=self.reason,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.vote_flow.why_no_submitted(
            interaction, self.plan_id, self.reason.value
        )


class VoteFlow:
    def __init__(self, bot: SquadBot) -> None:
        self.bot = bot
        self.tasks: set[asyncio.Task] = set()  # strong refs for persona votes

    def _channel(self, channel_id: str):
        cid = int(channel_id)
        return self.bot.get_channel(cid) or self.bot.get_partial_messageable(cid)

    def _names(self, plan: Plan) -> dict[str, str]:
        squad = self.bot.store.squad(plan.channel_id)
        ids = squad.member_ids if squad else []
        return {m.id: m.name for m in self.bot.store.members(ids)}

    def _poll_plan(self, message_id: int) -> Plan | None:
        return next(
            (
                p
                for p in self.bot.store.plans("polling")
                if p.poll_message_id == str(message_id)
            ),
            None,
        )

    async def _save_and_edit(self, plan: Plan) -> None:
        await self.bot.store.put_plan(plan)
        card = self._channel(plan.channel_id).get_partial_message(int(plan.message_id))
        try:
            await card.edit(
                view=plan_card(plan, self._names(plan), self.bot.settings.tz)
            )
        except discord.HTTPException as error:  # a deleted card must not lose votes
            log.info("card edit failed: %s", type(error).__name__)

    async def _post(self, plan: Plan, name: str, avatar: str, text: str) -> None:
        squad = self.bot.store.squad(plan.channel_id)
        try:
            webhook = await self.bot.webhook_for(squad, self._channel(plan.channel_id))
            await post_as(
                webhook, name, avatar, text, thread=discord.Object(int(plan.thread_id))
            )
        # no Manage Webhooks or a deleted webhook: the bot posts it itself
        except (AttributeError, discord.HTTPException) as error:
            log.info("thread post via webhook failed: %s", type(error).__name__)
            await self._channel(plan.thread_id).send(
                f"**{name}:** {text}", allowed_mentions=discord.AllowedMentions.none()
            )

    async def _remember(self, member_id: str, learned: LearnedFilter) -> bool:
        member = self.bot.store.member(member_id)  # fresh: they may have left
        if member is None:
            return False
        if all(
            (f.kind, f.value) != (learned.kind, learned.value)
            for f in member.learned_filters
        ):
            # a copy: stored personas are the shared PERSONAS objects
            filters = [*member.learned_filters, learned]
            await self.bot.store.put_member(
                member.model_copy(update={"learned_filters": filters})
            )
        return True

    async def on_raw_poll_vote_add(
        self, payload: discord.RawPollVoteActionEvent
    ) -> None:
        plan = self._poll_plan(payload.message_id)
        if plan is None or not 1 <= payload.answer_id <= len(VOTE_KEYS):
            return
        uid, vote = str(payload.user_id), VOTE_KEYS[payload.answer_id - 1]
        plan.votes[uid] = vote
        await self._save_and_edit(plan)
        squad = self.bot.store.squad(plan.channel_id)
        if (
            vote == "no"
            and squad
            and uid in squad.member_ids
            and uid not in plan.why_no_asked
        ):
            plan.why_no_asked.append(uid)
            await self.bot.store.put_plan(plan)
            await self.bot.dm(uid, view=why_no_view(plan.id))  # closed DMs: skipped

    async def on_raw_poll_vote_remove(
        self, payload: discord.RawPollVoteActionEvent
    ) -> None:
        plan = self._poll_plan(payload.message_id)
        if plan is None or not 1 <= payload.answer_id <= len(VOTE_KEYS):
            return
        uid = str(payload.user_id)
        # a changed vote can arrive as add-new before remove-old
        if plan.votes.get(uid) == VOTE_KEYS[payload.answer_id - 1]:
            del plan.votes[uid]
            await self._save_and_edit(plan)

    def schedule_persona_votes(self, plan: Plan) -> None:
        # returns None so run_plan doesn't await the 15-minute task
        task = asyncio.create_task(self.persona_votes(plan.id))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def persona_votes(self, plan_id: str) -> None:
        try:
            await self._persona_votes(plan_id)
        except Exception:
            log.exception("persona votes failed")

    async def _persona_votes(self, plan_id: str) -> None:
        store = self.bot.store
        delays = self.bot.settings.persona_vote_delays_s
        waited = 0
        for key, (i, vote, reason) in sorted(
            DEMO_VOTES.items(), key=lambda kv: kv[1][0]
        ):
            await asyncio.sleep(delays[i] - waited)  # delays count from the post
            waited = delays[i]
            plan = store.plan(plan_id)
            if plan is None or plan.status != "polling":
                return
            persona: Member | None = store.member(f"demo:{key}")
            squad = store.squad(plan.channel_id)
            if persona is None or squad is None or persona.id not in squad.member_ids:
                continue
            await self.persona_vote(plan, persona, vote)
            if reason:
                learned = await learn_from_no(self.bot.llm, persona, reason, plan.event)
                if learned:
                    await self.persona_learned(plan, persona, learned)

    async def persona_vote(self, plan: Plan, persona: Member, vote: str) -> None:
        plan.votes[persona.id] = vote
        await self._save_and_edit(plan)
        await self._post(plan, persona.name, persona.avatar_url, PERSONA_LINES[vote])

    async def persona_learned(
        self, plan: Plan, persona: Member, learned: LearnedFilter
    ) -> None:
        if await self._remember(persona.id, learned):
            await self._post(
                plan, f"{persona.name}'s agent", persona.avatar_url, JORDAN_LEARNED
            )

    async def why_no(self, interaction: discord.Interaction, plan_id: str) -> None:
        await interaction.response.send_modal(WhyNoModal(self, plan_id))

    async def why_no_submitted(
        self, interaction: discord.Interaction, plan_id: str, reason: str
    ) -> None:
        await interaction.response.defer(
            ephemeral=True, thinking=True
        )  # Claude can take >3 s
        uid = str(interaction.user.id)
        member, plan = self.bot.store.member(uid), self.bot.store.plan(plan_id)
        learned = None
        if member and plan and reason.strip():
            try:
                learned = await learn_from_no(self.bot.llm, member, reason, plan.event)
            # any failure still gets a thank-you, never a stuck "thinking…"
            except Exception as error:  # noqa: BLE001
                log.info("learn from no failed: %s", type(error).__name__)
        kept = learned is not None and await self._remember(uid, learned)
        await interaction.followup.send(KEPT if kept else THANKS, ephemeral=True)

    async def close_poll(self, interaction: discord.Interaction, plan_id: str) -> None:
        plan = self.bot.store.plan(plan_id)
        if plan is None:
            await interaction.response.send_message(GONE, ephemeral=True)
            return
        squad = self.bot.store.squad(plan.channel_id)
        if squad is None or str(interaction.user.id) not in squad.member_ids:
            await interaction.response.send_message(MEMBERS_ONLY, ephemeral=True)
            return
        if plan.status != "polling":
            await interaction.response.send_message(ALREADY_CLOSED, ephemeral=True)
            return
        await interaction.response.defer()
        poll = self._channel(plan.channel_id).get_partial_message(
            int(plan.poll_message_id)
        )
        try:
            await poll.end_poll()
        except discord.HTTPException as error:  # it may have just expired
            log.info("ending the poll failed: %s", type(error).__name__)
        await self.finish(plan)

    async def finish(self, plan: Plan) -> None:
        if plan.status == "closed":
            return
        store, tz = self.bot.store, self.bot.settings.tz
        plan.status = "closed"  # before any await, so a second caller returns
        await store.put_plan(plan)
        channel, thread = self._channel(plan.channel_id), self._channel(plan.thread_id)
        going_ids = [uid for uid, v in plan.votes.items() if v == "yes"]
        if not going_ids:
            for target in (channel, thread):
                await target.send(NOBODY)
            return

        event = plan.event
        rides = plan_rides(store.members(going_ids), event.location)
        guild = getattr(channel, "guild", None)
        if guild:
            try:
                scheduled = await guild.create_scheduled_event(
                    name=event.title[:100],
                    start_time=event.start,
                    end_time=event.end,
                    entity_type=discord.EntityType.external,
                    location=event.location[:100],
                    privacy_level=discord.PrivacyLevel.guild_only,
                    description=f"{plan.why}\n{event.url}"[:1000],
                )
                plan.discord_event_url = scheduled.url
                await store.put_plan(plan)
            # no Manage Events (or Discord said no): the results still post
            except discord.HTTPException as error:
                log.info("scheduled event failed: %s", type(error).__name__)
        names = self._names(plan)
        for target in (channel, thread):
            await target.send(view=results_card(plan, names, rides, tz))

    async def close_due(self, now: datetime) -> None:
        for plan in self.bot.store.plans("polling"):
            if plan.poll_closes_at and plan.poll_closes_at <= now:
                try:
                    await self.finish(plan)
                except Exception:
                    log.exception("closing a poll failed")


def setup(bot: SquadBot) -> None:
    flow = VoteFlow(bot)
    # discord.Client dispatches events to on_<event> attributes
    bot.on_raw_poll_vote_add = flow.on_raw_poll_vote_add
    bot.on_raw_poll_vote_remove = flow.on_raw_poll_vote_remove
    flows = bot.flows
    flows.schedule_persona_votes = flow.schedule_persona_votes
    flows.persona_vote = flow.persona_vote
    flows.persona_learned = flow.persona_learned
    flows.why_no = flow.why_no
    flows.close_poll = flow.close_poll
    flows.finish = flow.finish

    @tasks.loop(seconds=30)
    async def closer_loop() -> None:
        if bot.is_ready():
            await flow.close_due(datetime.now(bot.settings.tz))

    flows.closer_loop = closer_loop
    closer_loop.start()

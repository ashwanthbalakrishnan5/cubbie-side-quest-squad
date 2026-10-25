"""Discord client: slash commands, sign-up, leave, demo squad and DMs."""

from __future__ import annotations

import asyncio
import importlib
import logging
import re
from datetime import datetime, time, timedelta

import discord
from discord import app_commands, ui

from . import demo_script
from .calendar import CalendarLinker
from .config import Settings
from .llm import LLM
from .models import Squad
from .personas import INTRO_LINES, PERSONAS, post_as
from .store import Store
from .ui.cards import (
    CloseButton,
    ConfirmButton,
    Step2Button,
    WhyButton,
    WhyNoButton,
    _view,
)
from .ui.onboarding import (
    CallsModal,
    CallsValues,
    JoinModal,
    JoinValues,
    apply_calls,
    member_from_join,
)

log = logging.getLogger(__name__)

WARMING_UP = "Planning is warming up, try again in a sec"
NO_WEBHOOK = (
    "I can't bring demo friends in here. Try /squad demo in a server channel "
    "where I can manage webhooks 🙂"
)
DEMO_RETRY = "Couldn't bring everyone in just now. Try /squad demo again in a sec 🙂"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EVERYWHERE = app_commands.AppCommandContext(
    guild=True, dm_channel=True, private_channel=True
)
INSTALLS = app_commands.AppInstallationType(guild=True, user=True)


class Flows:
    """Attribute bag; this module adds sign-up flows, Tasks 12-14 add the rest via setup(bot)."""


def next_weekly_run(weekday: int, hour: int, now: datetime) -> datetime:
    day = now.date() + timedelta(days=(weekday - now.weekday()) % 7)
    run = datetime.combine(day, time(hour), now.tzinfo)
    return run if run > now else run + timedelta(days=7)


class SquadBot(discord.Client):
    def __init__(
        self,
        settings: Settings,
        store: Store,
        llm: LLM,
        calendar: CalendarLinker | None,
    ) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.polls = True
        super().__init__(
            intents=intents,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )
        self.settings = settings
        self.store = store
        self.llm = llm
        self.calendar = calendar
        self.tree = app_commands.CommandTree(self)
        self.flows = Flows()
        self.flows.join_submitted = self.join_submitted
        self.flows.open_step2 = self.open_step2
        self.flows.calls_submitted = self.calls_submitted

    async def setup_hook(self) -> None:
        await self.store.load()
        self.add_dynamic_items(
            CloseButton, WhyButton, ConfirmButton, WhyNoButton, Step2Button
        )
        self._register_commands()
        for name in ("plan_flow", "vote_flow", "nudge_flow"):
            module = f"squad.flows.{name}"
            try:
                importlib.import_module(module).setup(self)
            except ModuleNotFoundError as e:
                if e.name != module:
                    raise
                log.info("%s not built yet, skipping", module)
        await self.tree.sync()

    def _register_commands(self) -> None:
        group = app_commands.Group(
            name="squad",
            description="Plan one real campus hangout a week with your friends",
            allowed_contexts=EVERYWHERE,
            allowed_installs=INSTALLS,
        )

        @group.command(name="join", description="Join this channel's squad")
        async def join(interaction: discord.Interaction) -> None:
            existing = self.store.member(str(interaction.user.id))
            await interaction.response.send_modal(JoinModal(existing))

        @group.command(
            name="leave", description="Leave and forget everything I know about you"
        )
        async def leave(interaction: discord.Interaction) -> None:
            await self.leave(interaction)

        @group.command(
            name="demo", description="Run the scripted demo with four demo friends"
        )
        async def demo(interaction: discord.Interaction) -> None:
            await self.demo(interaction)

        @group.command(
            name="nudge", description="Nudge someone about this channel's poll now"
        )
        @app_commands.describe(member="Who to nudge (you if empty)")
        async def nudge(
            interaction: discord.Interaction, member: discord.User | None = None
        ) -> None:
            await self.flows.nudge_now(interaction, member or interaction.user)

        @group.command(name="plan", description="Plan a hangout now")
        @app_commands.describe(
            vibe="Anything in mind? e.g. free food, chill, Friday night"
        )
        async def plan(
            interaction: discord.Interaction, vibe: str | None = None
        ) -> None:
            await self.plan_from_interaction(interaction, vibe or "")

        @group.command(name="weekly", description="When should I plan every week?")
        @app_commands.choices(
            day=[app_commands.Choice(name=d, value=i) for i, d in enumerate(DAYS)]
        )
        async def weekly(
            interaction: discord.Interaction,
            day: app_commands.Choice[int],
            hour: app_commands.Range[int, 8, 21],
        ) -> None:
            await self.set_weekly(interaction, day.value, hour)

        async def plan_this(
            interaction: discord.Interaction, message: discord.Message
        ) -> None:
            await self.plan_from_interaction(interaction, message.content)

        self.tree.add_command(group)
        self.tree.add_command(
            app_commands.ContextMenu(
                name="Plan this",
                callback=plan_this,
                allowed_contexts=EVERYWHERE,
                allowed_installs=INSTALLS,
            )
        )

    async def squad_for(self, channel: discord.abc.Messageable) -> Squad:
        squad = self.store.squad(str(channel.id))
        if squad is None:
            guild = getattr(channel, "guild", None)
            squad = Squad(
                channel_id=str(channel.id), guild_id=str(guild.id) if guild else ""
            )
            await self.store.put_squad(squad)
        return squad

    async def webhook_for(
        self, squad: Squad, channel: discord.TextChannel
    ) -> discord.Webhook:
        if not squad.webhook_url:
            webhook = await channel.create_webhook(name="Squad Mode")
            squad.webhook_url = webhook.url
            await self.store.put_squad(squad)
            return webhook
        return discord.Webhook.from_url(squad.webhook_url, client=self)

    async def dm(
        self,
        user_id: str,
        *,
        content: str | None = None,
        view: ui.LayoutView | None = None,
    ) -> bool:
        if not user_id.isdigit():  # personas have no DMs
            return False
        try:
            user = self.get_user(int(user_id)) or await self.fetch_user(int(user_id))
            await user.send(content=content, view=view)
        except (discord.Forbidden, discord.NotFound):
            return False
        return True

    async def join_submitted(
        self, interaction: discord.Interaction, values: JoinValues
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        user = interaction.user
        uid = str(user.id)
        member = member_from_join(
            uid,
            user.display_name,
            user.display_avatar.url,
            values,
            self.store.member(uid),
        )
        await self.store.put_member(member)
        squad = await self.squad_for(interaction.channel)
        if uid not in squad.member_ids:
            squad.member_ids.append(uid)
            await self.store.put_squad(squad)

        row = ui.ActionRow(Step2Button())
        if self.calendar:
            try:
                url = await asyncio.to_thread(self.calendar.connect_url, uid)
            # no calendar link is fine; the user must still get the step 2 button
            except Exception as error:  # noqa: BLE001
                log.warning("calendar connect link failed: %s", type(error).__name__)
                url = None
            if url:
                row.add_item(ui.Button(label="Connect Google Calendar", url=url))
        view = _view(
            ui.TextDisplay("You're in 🎉 One more step:"),
            row,
            ui.TextDisplay("No calendar? I'll use the free times you ticked."),
        )
        await interaction.followup.send(view=view, ephemeral=True)

    async def open_step2(self, interaction: discord.Interaction) -> None:
        existing = self.store.member(str(interaction.user.id))
        await interaction.response.send_modal(CallsModal(existing))

    async def calls_submitted(
        self, interaction: discord.Interaction, values: CallsValues
    ) -> None:
        member = self.store.member(str(interaction.user.id))
        if member is None:  # an old step-2 button clicked after /squad leave
            await interaction.response.send_message(
                "Start with /squad join first 🙂", ephemeral=True
            )
            return
        try:
            member = apply_calls(member, values)
        except ValueError:
            await interaction.response.send_message(
                "That number doesn't look right. Try something like +1 480 555 0123.",
                ephemeral=True,
            )
            return
        await self.store.put_member(member)
        await interaction.response.send_message("Saved ✨", ephemeral=True)

    async def leave(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        uid = str(interaction.user.id)
        await self.store.delete_member(uid)
        text = (
            "Done. I forgot everything about you (calendar link too). "
            "Come back anytime with /squad join."
        )
        if self.calendar:
            try:
                await asyncio.to_thread(self.calendar.disconnect, uid)
            # the reply must not claim the calendar link is gone when it isn't
            except Exception as error:  # noqa: BLE001
                log.warning("calendar disconnect failed: %s", type(error).__name__)
                text = (
                    "Done. I forgot everything about you, but I couldn't reach the "
                    "calendar service. Run /squad leave again in a bit to unlink it."
                )
        await interaction.followup.send(text, ephemeral=True)

    async def demo(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        channel = interaction.channel
        squad = await self.squad_for(channel)
        new = [p for p in PERSONAS if p.id not in squad.member_ids]
        for persona in PERSONAS:
            if self.store.member(persona.id) is None:  # keeps learned filters
                await self.store.put_member(persona.model_copy(deep=True))
        if new:
            # webhooks live on the parent channel; thread posts go through it
            thread = channel if isinstance(channel, discord.Thread) else None
            try:
                webhook = await self.webhook_for(
                    squad, thread.parent if thread else channel
                )
                for p in new:
                    await post_as(
                        webhook,
                        p.name,
                        p.avatar_url,
                        INTRO_LINES[p.id.split(":", 1)[1]],
                        thread=thread,
                    )
                    # saved per intro, so a retry posts only the missing ones
                    squad.member_ids.append(p.id)
                    await self.store.put_squad(squad)
                    await asyncio.sleep(demo_script.INTRO_GAP_S)
            # AttributeError: DMs and user-install channels have no create_webhook
            except (AttributeError, discord.Forbidden) as error:
                log.info("demo intros failed: %s", type(error).__name__)
                await interaction.followup.send(NO_WEBHOOK, ephemeral=True)
                return
            except discord.HTTPException as error:
                log.info("demo intros failed: %s", type(error).__name__)
                if isinstance(error, discord.NotFound):
                    squad.webhook_url = ""  # deleted webhook; the retry makes a new one
                    await self.store.put_squad(squad)
                await interaction.followup.send(DEMO_RETRY, ephemeral=True)
                return
        uid = str(interaction.user.id)
        if self.store.member(uid) is None:  # an existing member keeps their answers
            member = demo_script.presenter(interaction.user, self.settings.demo_phone)
            await self.store.put_member(member)
        if uid not in squad.member_ids:
            squad.member_ids.append(uid)
            await self.store.put_squad(squad)
        await interaction.followup.send(demo_script.ROLLING, ephemeral=True)
        await demo_script.run(self, interaction, squad)

    async def plan_from_interaction(
        self, interaction: discord.Interaction, text: str
    ) -> None:
        flow = getattr(self.flows, "plan_requested_from_interaction", None)
        if flow is None:
            await interaction.response.send_message(WARMING_UP, ephemeral=True)
            return
        await flow(interaction, text)

    async def set_weekly(
        self, interaction: discord.Interaction, weekday: int, hour: int
    ) -> None:
        squad = await self.squad_for(interaction.channel)
        squad.weekly_weekday, squad.weekly_hour = weekday, hour
        await self.store.put_squad(squad)
        run = next_weekly_run(weekday, hour, datetime.now(self.settings.tz))
        await interaction.response.send_message(
            f"Done. I'll plan something every {DAYS[weekday]}. "
            f"Next one: <t:{int(run.timestamp())}:F> 🗓️",
            ephemeral=True,
        )

    async def on_message(self, message: discord.Message) -> None:
        # chat is read only for mentions and never stored
        if message.author.bot or message.webhook_id or self.user is None:
            return
        if self.user not in message.mentions:
            return
        text = re.sub(rf"<@!?{self.user.id}>", "", message.content).strip()
        flow = getattr(self.flows, "plan_requested", None)
        if flow is None:
            await message.reply(WARMING_UP)
            return
        await flow(message, text)

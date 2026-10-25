"""Components V2 cards and the persistent buttons on them."""

from __future__ import annotations

import re
from zoneinfo import ZoneInfo

import discord
from discord import ui

from squad.constants import BRAND
from squad.models import Event, Plan, Rides


def _view(*children: ui.Item) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*children, accent_colour=discord.Colour(BRAND)))
    return view


def _when(event: Event) -> str:
    unix = int(event.start.timestamp())
    return f"🕖 <t:{unix}:F> · <t:{unix}:R>"


def _where(event: Event) -> str:
    line = f"📍 {event.location}"
    if event.price_usd > 0:
        line += f" · ${event.price_usd:g}"
    if event.free_food:
        line += " · free food 🍕"
    return line


def _name(names: dict[str, str], uid: str) -> str:
    return names.get(uid, "a friend")


class CloseButton(ui.DynamicItem[ui.Button], template=r"squad:close:(?P<plan>\w+)"):
    def __init__(self, plan_id: str) -> None:
        super().__init__(
            ui.Button(
                label="Close poll now",
                style=discord.ButtonStyle.secondary,
                custom_id=f"squad:close:{plan_id}",
            )
        )
        self.plan_id = plan_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Button, match: re.Match[str]
    ) -> CloseButton:
        return cls(match["plan"])

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.client.flows.close_poll(interaction, self.plan_id)


class WhyButton(ui.DynamicItem[ui.Button], template=r"squad:why:(?P<plan>\w+)"):
    def __init__(self, plan_id: str) -> None:
        super().__init__(
            ui.Button(
                label="How did you pick this?",
                style=discord.ButtonStyle.secondary,
                custom_id=f"squad:why:{plan_id}",
            )
        )
        self.plan_id = plan_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Button, match: re.Match[str]
    ) -> WhyButton:
        return cls(match["plan"])

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.client.flows.explain(interaction, self.plan_id)


class ConfirmButton(
    ui.DynamicItem[ui.Button],
    template=r"squad:confirm:(?P<plan>\w+):(?P<answer>yes|no)",
):
    def __init__(self, plan_id: str, answer: str) -> None:
        yes = answer == "yes"
        super().__init__(
            ui.Button(
                label="Sure, count me in" if yes else "Pass on this one",
                style=discord.ButtonStyle.success
                if yes
                else discord.ButtonStyle.secondary,
                custom_id=f"squad:confirm:{plan_id}:{answer}",
            )
        )
        self.plan_id = plan_id
        self.answer = answer

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Button, match: re.Match[str]
    ) -> ConfirmButton:
        return cls(match["plan"], match["answer"])

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.client.flows.confirm(interaction, self.plan_id, self.answer)


class WhyNoButton(ui.DynamicItem[ui.Button], template=r"squad:whyno:(?P<plan>\w+)"):
    def __init__(self, plan_id: str) -> None:
        super().__init__(
            ui.Button(
                label="Tell you why",
                style=discord.ButtonStyle.primary,
                custom_id=f"squad:whyno:{plan_id}",
            )
        )
        self.plan_id = plan_id

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Button, match: re.Match[str]
    ) -> WhyNoButton:
        return cls(match["plan"])

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.client.flows.why_no(interaction, self.plan_id)


class Step2Button(ui.DynamicItem[ui.Button], template=r"squad:step2"):
    def __init__(self) -> None:
        super().__init__(
            ui.Button(
                label="Calls & quiet hours",
                style=discord.ButtonStyle.primary,
                custom_id="squad:step2",
            )
        )

    @classmethod
    async def from_custom_id(
        cls, interaction: discord.Interaction, item: ui.Button, match: re.Match[str]
    ) -> Step2Button:
        return cls()

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.client.flows.open_step2(interaction)


def who_line(plan: Plan, names: dict[str, str]) -> str:
    yes = [_name(names, u) for u, v in plan.votes.items() if v == "yes"]
    maybe = [_name(names, u) for u, v in plan.votes.items() if v == "maybe"]
    no = sum(v == "no" for v in plan.votes.values())
    parts = []
    if yes:
        parts.append("✅ " + ", ".join(yes))
    if maybe:
        parts.append("🤔 " + ", ".join(maybe))
    if no:
        parts.append(f"❌ {no} can't make it")
    return "  ".join(parts) or "Nobody's voted yet, no pressure 🙂"


def plan_card(plan: Plan, names: dict[str, str], tz: ZoneInfo) -> ui.LayoutView:
    event = plan.event
    items: list[ui.Item] = [
        ui.TextDisplay("## 🗺️ This week's side quest"),
        ui.TextDisplay(f"### {event.title}"),
        ui.TextDisplay(_when(event)),
        ui.TextDisplay(_where(event)),
        ui.TextDisplay(f"_{plan.headline}_"),
        ui.TextDisplay(plan.why),
    ]
    if plan.tradeoffs:
        items.append(
            ui.TextDisplay(
                "**Trade-offs**\n" + "\n".join("• " + t for t in plan.tradeoffs)
            )
        )
    items += [ui.Separator(), ui.TextDisplay(who_line(plan, names))]
    row = ui.ActionRow()
    if event.url:
        row.add_item(ui.Button(label="Event page", url=event.url))
    row.add_item(CloseButton(plan.id))
    row.add_item(WhyButton(plan.id))
    return _view(*items, row)


def results_card(
    plan: Plan, names: dict[str, str], rides: Rides, tz: ZoneInfo
) -> ui.LayoutView:
    event = plan.event
    going = [_name(names, u) for u, v in plan.votes.items() if v == "yes"]
    items: list[ui.Item] = [
        ui.TextDisplay("## 🎉 It's on"),
        ui.TextDisplay(f"### {event.title}"),
        ui.TextDisplay(_when(event)),
        ui.TextDisplay(_where(event)),
        ui.TextDisplay("**Going:** " + ", ".join(going)),
    ]
    lines = [
        f"🚗 {_name(names, c.driver_id)} → "
        + (", ".join(_name(names, r) for r in c.rider_ids) or "driving solo")
        for c in rides.cars
    ]
    if rides.transit_ids:
        transit = ", ".join(_name(names, u) for u in rides.transit_ids)
        lines.append(f"🚆 {transit}: {rides.transit_tip}")
    if lines:
        items.append(ui.TextDisplay("**Rides**\n" + "\n".join(lines)))
    if plan.discord_event_url:
        items.append(ui.TextDisplay(f"📅 [Discord event]({plan.discord_event_url})"))
    return _view(*items)


def no_plan_card(reason: str, near_miss: Event | None, tz: ZoneInfo) -> ui.LayoutView:
    items: list[ui.Item] = [
        ui.TextDisplay("## 🌙 No side quest this week"),
        ui.TextDisplay(reason),
    ]
    if near_miss:
        items.append(
            ui.TextDisplay(f"Closest call: **{near_miss.title}**\n{_when(near_miss)}")
        )
    return _view(*items)


def confirm_view(plan_id: str, text: str) -> ui.LayoutView:
    return _view(
        ui.TextDisplay(text),
        ui.ActionRow(ConfirmButton(plan_id, "yes"), ConfirmButton(plan_id, "no")),
    )


def why_no_view(plan_id: str) -> ui.LayoutView:
    skip = ui.Button(label="Skip", style=discord.ButtonStyle.secondary)

    async def on_skip(interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            view=_view(ui.TextDisplay("No worries 🙂"))
        )

    skip.callback = on_skip
    return _view(
        ui.TextDisplay(
            "Mind sharing why? Totally optional, it just helps me pick better next time."
        ),
        ui.ActionRow(WhyNoButton(plan_id), skip),
    )

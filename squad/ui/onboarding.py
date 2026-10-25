"""Two-step sign-up: JoinModal (tastes) then CallsModal (phone and quiet hours)."""

from __future__ import annotations

import re
from dataclasses import dataclass

import discord
from discord import ui

from squad.constants import BUDGETS, FREE_SLOTS, INTERESTS, NO_GO, QUIET_HOURS, SEATS
from squad.models import Member


@dataclass
class JoinValues:
    interests: list[str]
    free_slots: list[str]
    budget_key: str
    no_go: list[str]
    seats_key: str


@dataclass
class CallsValues:
    phone_raw: str
    call_opt_in: bool
    quiet_key: str


def _checks(choices: dict, picked: list[str]) -> list[discord.CheckboxGroupOption]:
    return [
        discord.CheckboxGroupOption(label=v[0], value=k, default=k in picked)
        for k, v in choices.items()
    ]


def _radios(choices: dict, picked: str | None) -> list[discord.RadioGroupOption]:
    return [
        discord.RadioGroupOption(label=v[0], value=k, default=k == picked)
        for k, v in choices.items()
    ]


def _budget_key(usd: int) -> str | None:
    return next((k for k, (_, v) in BUDGETS.items() if v == usd), None)


class JoinModal(ui.Modal, title="Join the squad (1/2)"):
    def __init__(self, existing: Member | None = None) -> None:
        super().__init__()
        m = existing
        self.interests = ui.CheckboxGroup(
            options=_checks(INTERESTS, m.interests if m else []),
            min_values=1,
            max_values=10,
        )
        self.free_slots = ui.CheckboxGroup(
            options=_checks(FREE_SLOTS, m.free_slots if m else []),
            min_values=1,
            max_values=6,
        )
        self.budget = ui.RadioGroup(
            options=_radios(BUDGETS, _budget_key(m.budget_usd) if m else None)
        )
        self.no_go = ui.CheckboxGroup(
            options=_checks(NO_GO, m.no_go if m else []),
            required=False,
            min_values=0,
            max_values=7,
        )
        self.seats = ui.RadioGroup(options=_radios(SEATS, str(m.seats) if m else None))
        self.add_item(ui.Label(text="What are you into?", component=self.interests))
        self.add_item(
            ui.Label(text="When are you usually free?", component=self.free_slots)
        )
        self.add_item(ui.Label(text="Budget per hangout", component=self.budget))
        self.add_item(
            ui.Label(text="Hard no's", description="Optional", component=self.no_go)
        )
        self.add_item(ui.Label(text="Do you drive?", component=self.seats))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = JoinValues(
            interests=list(self.interests.values),
            free_slots=list(self.free_slots.values),
            budget_key=self.budget.value or "free",
            no_go=list(self.no_go.values),
            seats_key=self.seats.value or "0",
        )
        await interaction.client.flows.join_submitted(interaction, values)


class CallsModal(ui.Modal, title="Join the squad (2/2)"):
    def __init__(self, existing: Member | None = None) -> None:
        super().__init__()
        m = existing
        self.phone = ui.TextInput(
            required=False,
            placeholder="+1 480 555 0123",
            max_length=20,
            default=m.phone if m and m.phone else None,
        )
        self.opt_in = ui.Checkbox(default=bool(m and m.call_opt_in))
        self.quiet = ui.RadioGroup(
            options=_radios(QUIET_HOURS, m.quiet_hours if m else "22-9")
        )
        self.add_item(ui.Label(text="WhatsApp number", component=self.phone))
        self.add_item(
            ui.Label(
                text="Voice nudge",
                description="One friendly call if you miss a plan poll",
                component=self.opt_in,
            )
        )
        self.add_item(ui.Label(text="Quiet hours", component=self.quiet))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = CallsValues(
            phone_raw=self.phone.value,
            call_opt_in=self.opt_in.value,
            quiet_key=self.quiet.value or "22-9",
        )
        await interaction.client.flows.calls_submitted(interaction, values)


def member_from_join(
    member_id: str,
    name: str,
    avatar_url: str,
    v: JoinValues,
    existing: Member | None,
) -> Member:
    fields = {
        "id": member_id,
        "name": name,
        "avatar_url": avatar_url,
        "interests": v.interests,
        "free_slots": v.free_slots,
        "budget_usd": BUDGETS[v.budget_key][1],
        "no_go": v.no_go,
        "seats": SEATS[v.seats_key][1],
    }
    if existing:
        return existing.model_copy(update=fields)
    return Member(**fields)


def apply_calls(member: Member, v: CallsValues) -> Member:
    raw = v.phone_raw.strip()
    if not raw:
        return member.model_copy(
            update={"phone": "", "call_opt_in": False, "quiet_hours": v.quiet_key}
        )
    digits = re.sub(r"\D", "", raw)
    if not re.fullmatch(r"\+?[\d\s\-()]+", raw) or not 10 <= len(digits) <= 15:
        raise ValueError("phone")
    if len(digits) == 10 and not raw.startswith("+"):
        digits = "1" + digits
    return member.model_copy(
        update={
            "phone": "+" + digits,
            "call_opt_in": v.call_opt_in,
            "quiet_hours": v.quiet_key,
        }
    )

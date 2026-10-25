"""Shared data models. All datetimes are timezone-aware."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class BusyBlock(BaseModel):
    start: datetime
    end: datetime


class LearnedFilter(BaseModel):
    kind: Literal["max_price", "latest_start_hour", "no_tag", "no_weekday", "note"]
    value: str
    source_text: str
    created_at: datetime


class Member(BaseModel):
    id: str  # Discord user id as str, or "demo:<name>" for personas
    name: str
    is_demo: bool = False
    avatar_url: str = ""
    interests: list[str]
    free_slots: list[str]
    budget_usd: int
    no_go: list[str] = []
    seats: int = 0
    phone: str = ""
    call_opt_in: bool = False
    quiet_hours: str = "22-9"
    learned_filters: list[LearnedFilter] = []
    demo_busy: list[BusyBlock] = []


class Event(BaseModel):
    id: str  # sha1(title + start.isoformat())[:10]
    title: str
    start: datetime
    end: datetime
    location: str
    org: str = ""
    description: str = ""
    url: str = ""
    tags: list[str] = []
    free_food: bool = False
    price_usd: float = 0.0


class Request(BaseModel):
    vibe: str = ""
    max_price: float | None = None
    weekdays: list[int] = []
    earliest_hour: int | None = None
    latest_hour: int | None = None
    exclude_no_go: list[str] = []
    keywords: list[str] = []


class Violation(BaseModel):
    member_id: str
    kind: Literal["busy", "budget", "no_go", "late", "learned"]
    detail_private: str  # only ever shown to that member
    label_public: str  # safe for the group


class Stance(BaseModel):
    member_id: str
    event_id: str
    score: int
    shared_reason: str
    flex_ok: bool


class Decision(BaseModel):
    event_id: str
    headline: str
    why: str
    tradeoffs: list[str]


class AgentTurn(BaseModel):
    speaker: str
    member_id: str | None = None
    text: str


class Car(BaseModel):
    driver_id: str
    rider_ids: list[str]


class Rides(BaseModel):
    cars: list[Car]
    transit_ids: list[str]
    transit_tip: str


class Squad(BaseModel):
    channel_id: str
    guild_id: str
    member_ids: list[str] = []
    weekly_weekday: int = 2
    weekly_hour: int = 18
    poll_hours: int = 1
    webhook_url: str = ""
    last_weekly_date: date | None = None


class Plan(BaseModel):
    id: str
    channel_id: str
    event: Event
    status: Literal["confirming", "polling", "closed", "cancelled"] = "confirming"
    headline: str
    why: str
    tradeoffs: list[str] = []
    ask_first: list[str] = []
    confirmations: dict[str, bool] = {}
    declined_event_ids: list[str] = []
    turns: list[AgentTurn] = []
    message_id: str = ""
    thread_id: str = ""
    poll_message_id: str = ""
    poll_closes_at: datetime | None = None
    votes: dict[str, Literal["yes", "maybe", "no"]] = {}
    why_no_asked: list[str] = []
    nudged: list[str] = []
    discord_event_url: str = ""
    created_at: datetime


class NoPlan(BaseModel):
    reason: str
    near_miss: Event | None = None

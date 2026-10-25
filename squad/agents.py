"""Per-member Claude agents, the coordinator, and their deterministic fallbacks."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from . import prompts
from .constants import BUDGETS, INTERESTS, NO_GO
from .llm import LLM, LLMError
from .matching import interest_score
from .models import Decision, Event, LearnedFilter, Member, Request, Stance, Violation

TZ = ZoneInfo("America/Phoenix")
Candidates = list[tuple[Event, list[Violation]]]


class RequestOut(BaseModel):
    vibe: str = ""
    max_price: float | None = None
    weekdays: list[int] = []
    earliest_hour: int | None = None
    latest_hour: int | None = None
    exclude_no_go: list[str] = []
    keywords: list[str] = []


class StanceOut(BaseModel):
    event_id: str
    score: int
    shared_reason: str
    flex_ok: bool


class StancesOut(BaseModel):
    stances: list[StanceOut]


class DecisionOut(BaseModel):
    event_id: str
    headline: str
    why: str
    tradeoffs: list[str]


class LearnedOut(BaseModel):
    kind: Literal["max_price", "latest_start_hour", "no_tag", "no_weekday", "note"]
    value: str
    keep: bool


def _when(event: Event) -> str:
    return f"{event.start.astimezone(TZ):%a %b %-d, %-I:%M %p}"


def _event_line(event: Event) -> str:
    price = f"${event.price_usd:g}" if event.price_usd else "free"
    return f"{event.title} | {_when(event)} | {event.location} | {price}"


async def parse_request(llm: LLM, text: str, now: datetime) -> Request:
    user = f"Today is {now.astimezone(TZ):%A %Y-%m-%d %H:%M}.\nAsk: {text}"
    try:
        out = await llm.parse(
            system=prompts.REQUEST_SYSTEM, user=user, schema=RequestOut, effort="low"
        )
    except LLMError:
        return Request(vibe=text)
    data = out.model_dump()
    data["exclude_no_go"] = [k for k in out.exclude_no_go if k in NO_GO]
    data["weekdays"] = [d for d in out.weekdays if 0 <= d <= 6]
    return Request(**data)


def _fallback_stance(member: Member, event: Event) -> Stance:
    return Stance(
        member_id=member.id,
        event_id=event.id,
        score=min(10, 3 * interest_score(member, event)),
        shared_reason="",
        flex_ok=False,
    )


def _profile(member: Member) -> str:
    budget = next(
        (label for label, usd in BUDGETS.values() if usd == member.budget_usd),
        f"${member.budget_usd}",
    )
    lines = [
        f"Name: {member.name}",
        "Interests: "
        + ", ".join(INTERESTS[k][0] for k in member.interests if k in INTERESTS),
        f"Budget: {budget}",
        "Hard no: "
        + (", ".join(NO_GO[k][0] for k in member.no_go if k in NO_GO) or "none"),
    ]
    lines += [
        f"Learned: {f.kind} {f.value} ({f.source_text})" for f in member.learned_filters
    ]
    return "\n".join(lines)


async def member_stances(
    llm: LLM, member: Member, candidates: Candidates, request: Request
) -> list[Stance]:
    blocks = []
    for event, violations in candidates:
        mine = [v.detail_private for v in violations if v.member_id == member.id]
        blocks.append(
            f"- event_id {event.id}: {_event_line(event)}\n"
            f"  {event.description[:300]}\n"
            f"  Limits it breaks for {member.name}: {'; '.join(mine) or 'none'}"
        )
    user = (
        f"Private profile:\n{_profile(member)}\n\nThe group asked for: "
        f"{request.vibe or 'anything fun'}\n\nCandidates:\n" + "\n".join(blocks)
    )
    by_id: dict[str, StanceOut] = {}
    try:
        out = await llm.parse(
            system=prompts.MEMBER_SYSTEM.format(name=member.name),
            user=user,
            schema=StancesOut,
            effort="low",
        )
        for s in out.stances:
            by_id.setdefault(s.event_id, s)
    except LLMError:
        pass
    stances = []
    for event, _ in candidates:
        s = by_id.get(event.id)
        if s is None:
            stances.append(_fallback_stance(member, event))
            continue
        stances.append(
            Stance(
                member_id=member.id,
                event_id=event.id,
                score=max(0, min(10, s.score)),
                shared_reason=s.shared_reason[:120],
                flex_ok=s.flex_ok,
            )
        )
    return stances


def fallback_decision(
    members: list[Member], candidates: Candidates, stances: list[Stance]
) -> Decision:
    def key(c: tuple[Event, list[Violation]]):
        event, violations = c
        total = sum(s.score for s in stances if s.event_id == event.id)
        return (len(violations), -total, event.start)

    event, violations = min(candidates, key=key)
    tradeoffs = list(dict.fromkeys(f"Someone has {v.label_public}" for v in violations))
    return Decision(
        event_id=event.id,
        headline=f"{event.title}, {event.start.astimezone(TZ):%a %-I:%M %p}",
        why="It's the option that fits the most of you this week.",
        tradeoffs=tradeoffs[:3],
    )


async def coordinate(
    llm: LLM,
    members: list[Member],
    candidates: Candidates,
    stances: list[Stance],
    request: Request,
) -> Decision:
    names = {m.id: m.name for m in members}
    blocks = []
    for event, violations in candidates:
        votes = [
            f"  {names.get(s.member_id, '?')}: {s.score}/10"
            + (f' "{s.shared_reason}"' if s.shared_reason else "")
            for s in stances
            if s.event_id == event.id
        ]
        limits = [
            f"{names.get(v.member_id, '?')}: {v.label_public}" for v in violations
        ]
        blocks.append(
            f"- event_id {event.id}: {_event_line(event)}\n"
            + "\n".join(votes)
            + f"\n  Broken limits: {'; '.join(limits) or 'none'}"
        )
    user = (
        f"The group asked for: {request.vibe or 'anything fun'}\n\n"
        "Candidates:\n" + "\n".join(blocks)
    )
    try:
        out = await llm.parse(
            system=prompts.COORDINATOR_SYSTEM,
            user=user,
            schema=DecisionOut,
            effort="medium",
        )
    except LLMError:
        return fallback_decision(members, candidates, stances)
    if out.event_id not in {e.id for e, _ in candidates}:
        return fallback_decision(members, candidates, stances)
    return Decision(
        event_id=out.event_id,
        headline=out.headline[:80],
        why=out.why[:280],
        tradeoffs=[t[:120] for t in out.tradeoffs[:3]],
    )


async def learn_from_no(
    llm: LLM, member: Member, reason: str, event: Event
) -> LearnedFilter | None:
    user = (
        f"{member.name} skipped: {_event_line(event)} "
        f"(tags: {', '.join(event.tags) or 'none'})\nTheir reason: {reason}"
    )
    try:
        out = await llm.parse(
            system=prompts.LEARN_SYSTEM, user=user, schema=LearnedOut, effort="low"
        )
    except LLMError:
        return None
    if not out.keep:
        return None
    return LearnedFilter(
        kind=out.kind,
        value=out.value,
        source_text=reason[:140],
        created_at=datetime.now(TZ),
    )

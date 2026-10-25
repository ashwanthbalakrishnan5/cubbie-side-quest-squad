"""Pick candidate events, ask every member's agent, and turn the coordinator's pick into a Plan."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from .agents import coordinate, member_stances
from .constants import CANDIDATES_K
from .constraints import request_allows, violations_for
from .llm import LLM
from .matching import interest_score
from .models import (
    AgentTurn,
    BusyBlock,
    Event,
    Member,
    NoPlan,
    Plan,
    Request,
    Violation,
)

LEAD = timedelta(minutes=90)  # events starting sooner than this are too late to plan


def pick_candidates(
    members: list[Member],
    events: list[Event],
    busy: dict[str, list[BusyBlock] | None],
    request: Request,
    tz,
    exclude: set[str],
) -> list[tuple[Event, list[Violation]]]:
    scored = []
    for event in events:
        if event.id in exclude or not request_allows(event, request, tz):
            continue
        violations = [
            v for m in members for v in violations_for(m, event, busy.get(m.id), tz)
        ]
        key = (
            len({v.member_id for v in violations}),
            -sum(interest_score(m, event) for m in members),
            event.start,
        )
        scored.append((key, event, violations))
    scored.sort(key=lambda s: s[0])
    return [(e, v) for _, e, v in scored[:CANDIDATES_K]]


async def build_plan(
    *,
    members: list[Member],
    events: list[Event],
    busy: dict[str, list[BusyBlock] | None],
    request: Request,
    llm: LLM,
    now: datetime,
    channel_id: str,
    tz,
    exclude: set[str] = frozenset(),
) -> Plan | NoPlan:
    if not members:
        return NoPlan(
            reason="Nobody's in the squad yet. Try /squad join or /squad demo."
        )
    events = [e for e in events if e.start >= now + LEAD]
    candidates = pick_candidates(members, events, busy, request, tz, exclude)
    if not candidates:
        return NoPlan(
            reason="Nothing on Sun Devil Central fits this week.", near_miss=None
        )
    per_member = await asyncio.gather(
        *(member_stances(llm, m, candidates, request) for m in members)
    )
    stances = [s for group in per_member for s in group]
    decision = await coordinate(llm, members, candidates, stances, request)
    event, violations = next(c for c in candidates if c[0].id == decision.event_id)
    ask_first = list(dict.fromkeys(v.member_id for v in violations))
    reasons = {s.member_id: s.shared_reason for s in stances if s.event_id == event.id}
    turns = [
        AgentTurn(speaker=f"{m.name}'s agent", member_id=m.id, text=reasons[m.id])
        for m in members
        if reasons.get(m.id)
    ]
    turns.append(AgentTurn(speaker="Coordinator", member_id=None, text=decision.why))
    return Plan(
        id=uuid4().hex[:10],
        channel_id=channel_id,
        event=event,
        status="confirming" if ask_first else "polling",
        headline=decision.headline,
        why=decision.why,
        tradeoffs=decision.tradeoffs,
        ask_first=ask_first,
        turns=turns,
        created_at=now,
    )

"""Keyword matching shared by the rules, the agents and the planner."""

from __future__ import annotations

from .constants import INTERESTS
from .models import Event, Member


def _searchable(event: Event) -> str:
    return " ".join(
        [event.title, event.description, event.org, " ".join(event.tags)]
    ).lower()


def keyword_hits(event: Event, keywords: list[str]) -> list[str]:
    text = _searchable(event)
    hits = []
    for keyword in keywords:
        k = keyword.lower()
        # "board games" should match "Board Game Night"
        singular = k[:-1] if len(k) >= 4 and k.endswith("s") else k
        if k in text or singular in text:
            hits.append(keyword)
    return hits


def interest_score(member: Member, event: Event) -> int:
    return sum(
        1
        for key in member.interests
        if key in INTERESTS and keyword_hits(event, INTERESTS[key][1])
    )

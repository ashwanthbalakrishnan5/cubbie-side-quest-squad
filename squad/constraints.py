"""Hard rules: the group's request filters and each member's private limits."""

from __future__ import annotations

import re
from datetime import datetime, time
from zoneinfo import ZoneInfo

from .availability import is_free
from .constants import NO_GO
from .matching import _searchable, keyword_hits
from .models import BusyBlock, Event, LearnedFilter, Member, Request, Violation


def _no_go_hit(key: str, text: str) -> bool:
    regex = NO_GO.get(key, ("", None))[1]
    return regex is not None and re.search(regex, text, re.IGNORECASE) is not None


def request_allows(event: Event, request: Request, tz: ZoneInfo) -> bool:
    start = event.start.astimezone(tz)
    text = _searchable(event)
    return (
        (request.max_price is None or event.price_usd <= request.max_price)
        and (not request.weekdays or start.weekday() in request.weekdays)
        and (request.earliest_hour is None or start.hour >= request.earliest_hour)
        and (request.latest_hour is None or start.hour < request.latest_hour)
        and not any(_no_go_hit(k, text) for k in request.exclude_no_go)
        and (not request.keywords or bool(keyword_hits(event, request.keywords)))
    )


def _learned_hit(f: LearnedFilter, event: Event, start: datetime, text: str) -> bool:
    # values come from parsed chat replies; a malformed one is ignored, not fatal
    try:
        return _learned_rule(f, event, start, text)
    except (ValueError, re.error):
        return False


def _learned_rule(f: LearnedFilter, event: Event, start: datetime, text: str) -> bool:
    if f.kind == "max_price":
        return event.price_usd > float(f.value)
    if f.kind == "latest_start_hour":
        return start.hour >= int(f.value)
    if f.kind == "no_tag":
        return re.search(f.value, text, re.IGNORECASE) is not None
    if f.kind == "no_weekday":
        return start.weekday() == int(f.value)
    return False  # "note" is context for the agents, never a rule


def violations_for(
    member: Member, event: Event, busy: list[BusyBlock] | None, tz: ZoneInfo
) -> list[Violation]:
    start = event.start.astimezone(tz)
    text = _searchable(event)
    out: list[tuple[str, str, str]] = []
    if not is_free(member, event.start, event.end, busy, tz):
        out.append(("busy", "you look busy then", "a schedule clash"))
    if event.price_usd > member.budget_usd:
        detail = f"it's ${event.price_usd:g} and your cap is ${member.budget_usd}"
        out.append(("budget", detail, "a budget limit"))
    for key in member.no_go:
        if _no_go_hit(key, text):
            detail = f"it looks like {NO_GO[key][0].lower()}"
            out.append(("no_go", detail, "a no-go type"))
    ten_pm = datetime.combine(start.date(), time(22), tzinfo=tz)
    if "late" in member.no_go and (start.hour >= 22 or event.end > ten_pm):
        out.append(("late", "it runs past 10pm", "a late-night limit"))
    for f in member.learned_filters:
        if _learned_hit(f, event, start, text):
            out.append(("learned", f.source_text, "something they told me before"))
    return [
        Violation(member_id=member.id, kind=k, detail_private=d, label_public=p)
        for k, d, p in out
    ]

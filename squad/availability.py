"""Who is free when: free-time slots, calendar busy blocks, quiet hours."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .constants import FREE_SLOTS, QUIET_HOURS, TRAVEL_MIN
from .models import BusyBlock, Member


def slot_covers(slot_key: str, start: datetime, end: datetime, tz: ZoneInfo) -> bool:
    if slot_key not in FREE_SLOTS:
        return False
    _, weekdays, start_hour, end_hour = FREE_SLOTS[slot_key]
    start = start.astimezone(tz)
    day = datetime.combine(start.date(), time(), tzinfo=tz)
    return (
        start.weekday() in weekdays
        and day + timedelta(hours=start_hour) <= start
        and end.astimezone(tz) <= day + timedelta(hours=end_hour)
    )


def is_free(
    member: Member,
    start: datetime,
    end: datetime,
    busy: list[BusyBlock] | None,
    tz: ZoneInfo,
) -> bool:
    if busy is None:
        return any(slot_covers(s, start, end, tz) for s in member.free_slots)
    leave_at = start - timedelta(minutes=TRAVEL_MIN)
    return not any(b.start < end and b.end > leave_at for b in busy)


def in_quiet_hours(member: Member, at: datetime, tz: ZoneInfo) -> bool:
    _, begin, until = QUIET_HOURS.get(member.quiet_hours, QUIET_HOURS["22-9"])
    hour = at.astimezone(tz).hour
    if begin < until:
        return begin <= hour < until
    return hour >= begin or hour < until

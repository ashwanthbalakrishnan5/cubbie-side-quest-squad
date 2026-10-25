"""Test doubles and factories shared by every test module."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from squad.constants import FREE_SLOTS
from squad.llm import LLMError
from squad.models import Event, Member

TZ = ZoneInfo("America/Phoenix")


class FakeLLM:
    """Returns queued objects per output schema; an exception instance in the queue is raised."""

    def __init__(self) -> None:
        self.queue: dict[type, list] = {}
        self.calls: list[dict] = []

    def push(self, schema: type, item) -> None:
        self.queue.setdefault(schema, []).append(item)

    async def parse(self, *, system: str, user: str, schema: type, effort: str):
        self.calls.append(
            {"system": system, "user": user, "schema": schema, "effort": effort}
        )
        items = self.queue.get(schema) or []
        if not items:
            raise LLMError(f"nothing queued for {schema.__name__}")
        item = items.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def make_member(id: str = "u1", **overrides) -> Member:
    data = {
        "id": id,
        "name": overrides.pop("name", id.capitalize()),
        "interests": ["music"],
        "free_slots": list(FREE_SLOTS),
        "budget_usd": 20,
        "seats": 0,
    }
    data.update(overrides)
    return Member(**data)


def make_event(
    title: str = "Open Mic Night", start: datetime | None = None, **overrides
) -> Event:
    from datetime import timedelta
    from hashlib import sha1

    start = start or datetime(2026, 10, 30, 19, 0, tzinfo=TZ)
    data = {
        "id": sha1(f"{title}{start.isoformat()}".encode()).hexdigest()[:10],
        "title": title,
        "start": start,
        "end": start + timedelta(hours=2),
        "location": "Memorial Union 202, Tempe Campus",
    }
    data.update(overrides)
    return Event(**data)

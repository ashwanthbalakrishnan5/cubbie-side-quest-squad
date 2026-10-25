"""Upcoming campus events from Sun Devil Central, with a memory cache and a 48 h file fallback."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta
from hashlib import sha1

from . import campus_events
from .config import Settings
from .constants import EVENT_HOURS
from .models import Event

MEMORY_TTL = timedelta(hours=6)
FILE_TTL = timedelta(hours=48)
PRICE = re.compile(r"\$(\d+(?:\.\d+)?)")

# (data_dir, url, campus, days) -> (fetched_at, events)
_memory: dict[tuple, tuple[datetime, list[Event]]] = {}


class EventsUnavailable(Exception):
    """The feed failed and there is no cache young enough to serve."""


def price_from_text(text: str) -> float:
    match = PRICE.search(text)
    return float(match.group(1)) if match else 0.0


def to_event(raw: dict) -> Event:
    start = raw["start"]
    return Event(
        id=sha1(f"{raw['title']}{start.isoformat()}".encode()).hexdigest()[:10],
        title=raw["title"],
        start=start,
        end=start + timedelta(hours=EVENT_HOURS),
        location=raw["location"],
        org=raw.get("org", ""),
        description=raw.get("description", ""),
        url=raw.get("url", ""),
        tags=raw.get("tags", []),
        free_food=raw.get("free_food", False),
        price_usd=price_from_text(f"{raw['title']} {raw.get('description', '')}"),
    )


def _fetch(settings: Settings, now: datetime, days: int) -> list[Event]:
    end = now + timedelta(days=days)
    raw = campus_events.read_feed(settings.events_url, now, end, settings.tz)
    ranked = campus_events.rank(raw, now, end, [], settings.campus)
    return [to_event(e) for e in ranked if not e["likely_skip"]]


async def upcoming_events(
    settings: Settings, now: datetime, days: int = 7
) -> list[Event]:
    key = (settings.data_dir, settings.events_url, settings.campus, days)
    hit = _memory.get(key)
    if hit and now - hit[0] < MEMORY_TTL:
        return [e for e in hit[1] if e.start > now]

    cache = settings.data_dir / "events_cache.json"
    try:
        found = await asyncio.to_thread(_fetch, settings, now, days)
    except (Exception, SystemExit) as exc:  # the script exits on feed errors
        try:
            doc = json.loads(cache.read_text())
            if now - datetime.fromisoformat(doc["fetched_at"]) < FILE_TTL:
                cached = [Event.model_validate(e) for e in doc["events"]]
                return [e for e in cached if e.start > now]
        except (OSError, ValueError, KeyError, TypeError):
            pass  # missing or corrupt cache: same as no cache
        raise EventsUnavailable("Sun Devil Central isn't answering") from exc

    _memory[key] = (now, found)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "fetched_at": now.isoformat(),
                "events": [e.model_dump(mode="json") for e in found],
            }
        )
    )
    return found

#!/usr/bin/env python3
"""List upcoming in-person campus events from a school's public events feed.

Reads the feed types most campuses publish, with no sign-in:
  - CampusGroups          its /rss_events feed (ASU's Sun Devil Central, and many others)
  - Engage / CampusLabs   https://<school>.campuslabs.com/engage
  - Localist              https://events.<school>.edu (its /api/2/events JSON)
  - iCalendar (.ics)      any calendar export link (Presence, 25Live, Google Calendar...)

Events are ranked by how well they match the student's interests, then by start time. Online-only and
all-day events are dropped, since a side quest happens in person at a set time. Cubbie passes the student's local date
and time zone, because the sandbox clock may be elsewhere.

Exit codes: 0 ok, 2 bad arguments, 3 no in-person events in the window, 4 feed unreachable,
5 not a feed this script can read (read the page with the web or browser instead).
"""

from __future__ import annotations

import argparse
import functools
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from xml.etree import ElementTree
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SAMPLE = Path(__file__).parent / "assets" / "sample_campusgroups.xml"
SAMPLE_DAY = date(2026, 10, 26)
HIDDEN_PLACE = "location on the event page"
PAGE_SIZE, MAX_PAGES = 100, 6
# Too late to make it to anything starting sooner than this.
SOONEST = timedelta(minutes=30)
ONLINE = re.compile(
    r"\b(online|virtual|zoom|teams meeting|webinar|livestream)\b", re.IGNORECASE
)
# Private by nature: never suggested as a social quest, whatever the interests.
NEVER = re.compile(
    r"\b(alcoholics anonymous|al-anon|alateen|narcotics anonymous|smart recovery"
    r"|recovery (meeting|group|community)|12-step|twelve step|support group|grief"
    r"|bereavement|therapy group|counseling group)\b",
    re.IGNORECASE,
)
# Not newcomer quests: ranked last unless they match the student's interests.
LIKELY_SKIP = re.compile(
    r"\b(church|worship|bible|prayer|ministry|chapter meeting|e-?board|officers? meeting"
    r"|members only|graduate students only|tabling|fundrais\w*|donation|campaign"
    r"|republican\w*|democrat\w*|socialis\w*|conservative\w*|libertarian\w*|canvassing)\b",
    re.IGNORECASE,
)
FREE_FOOD = re.compile(
    r"\b(free food|pizza|snacks|refreshments|food provided|free lunch|free dinner"
    r"|boba|donuts|tacos)\b",
    re.IGNORECASE,
)
BAD_ITEM = (KeyError, TypeError, ValueError, AttributeError)
WEEKDAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def fail(message: str, code: int):
    print(message, file=sys.stderr)
    sys.exit(code)


def fetch(url: str, quiet: bool = False) -> str:
    """Download a feed. With quiet, a guess that doesn't exist returns '' instead of exiting."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "side-quests-skill/1.0", "Accept": "*/*"}
    )
    try:
        # Per read, not per download: ASU's 6 MB feed takes ~25 s before its first byte.
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if quiet:
            return ""
        fail(f"The events feed returned HTTP {exc.code}: {url}", 4)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if quiet:
            return ""
        fail(f"Could not reach the events feed ({type(exc).__name__}): {url}", 4)


def json_dict(text: str) -> dict | None:
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def clean(text: str | None, limit: int = 0) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))
    text = re.sub(r"\s+", " ", text).strip()
    return text[: limit - 1].rstrip() + "…" if limit and len(text) > limit else text


def parse_iso(text: str) -> datetime:
    # Some feeds write 7-digit fractions ("19:00:00.0000000-07:00") that older Pythons reject.
    moment = datetime.fromisoformat(
        re.sub(r"\.\d+", "", text.strip()).replace("Z", "+00:00")
    )
    if moment.tzinfo is None:
        raise ValueError("start time without a time zone")
    return moment


def event(
    title, start, location="", org="", description="", tags=(), free_food=False, url=""
) -> dict:
    return {
        "title": clean(title),
        "start": start,
        "location": clean(location),
        "org": clean(org),
        "description": clean(description),
        "tags": [str(t) for t in tags if t],
        "free_food": free_food,
        "url": url or "",
    }


# ---------- CampusGroups ----------


def item_text(item: ElementTree.Element, name: str) -> str:
    return (item.findtext(name) or "").strip()


def from_campusgroups(text: str) -> list[dict]:
    events = []
    for item in ElementTree.fromstring(text).iter("item"):
        field = functools.partial(item_text, item)
        if (
            field("locationType") == "Virtual"
            or field("eventDelete") == "1"
            or field("allDayEvent") == "1"
        ):
            continue
        try:
            start = parse_iso(field("eventStartDateTime"))
        except ValueError:
            continue
        place = clean(field("eventLocation"))
        if not place or place.startswith("Private Location"):
            # Students see the room after signing in to the school's site.
            place = HIDDEN_PLACE
        topics = [t.text for t in item.iter("eventTopic") if t.text]
        events.append(
            event(
                field("title"),
                start,
                place,
                field("group"),
                field("fullDescription") or field("description"),
                topics + [field("eventType")],
                url=field("eventLink") or field("link"),
            )
        )
    return events


# ---------- Engage / CampusLabs ----------


def engage_site(host: str) -> str:
    # Engage lives at <school>.campuslabs.com/engage or on a school domain's root.
    return (
        f"https://{host}/engage"
        if host.endswith("campuslabs.com")
        else f"https://{host}"
    )


def engage_url(site: str, start: datetime, skip: int) -> str:
    query = urllib.parse.urlencode(
        {
            "endsAfter": start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "orderByField": "endsOn",
            "orderByDirection": "ascending",
            "status": "Approved",
            "take": PAGE_SIZE,
            "skip": skip,
        }
    )
    return f"{site}/api/discovery/event/search?{query}"


def from_engage(data: dict, site: str) -> list[dict]:
    events = []
    items = data.get("value")
    for e in items if isinstance(items, list) else []:
        try:
            if e.get("visibility") not in (None, "Public"):
                continue
            benefits = e.get("benefitNames") or []
            events.append(
                event(
                    e.get("name"),
                    parse_iso(e["startsOn"]),
                    e.get("location"),
                    e.get("organizationName"),
                    e.get("description"),
                    list(e.get("categoryNames") or []) + list(benefits),
                    "Free Food" in benefits,
                    f"{site}/event/{e['id']}",
                )
            )
        except BAD_ITEM:
            continue
    return events


def read_engage(site: str, start: datetime, end: datetime, quiet: bool) -> list | None:
    events: list[dict] = []
    for page in range(MAX_PAGES):
        data = json_dict(fetch(engage_url(site, start, page * PAGE_SIZE), quiet))
        if not data or not isinstance(data.get("value"), list):
            return events if page else None
        batch = from_engage(data, site)
        events += batch
        # Sorted by end time, so once a whole page starts after the window, stop.
        if len(data["value"]) < PAGE_SIZE or (
            batch and min(e["start"] for e in batch) >= end
        ):
            break
    return events


# ---------- Localist ----------


def localist_url(base: str, day: date, days: int, page: int = 1) -> str:
    query = urllib.parse.urlencode(
        {"start": day.isoformat(), "days": days, "pp": PAGE_SIZE, "page": page}
    )
    return f"{base}/api/2/events?{query}"


def from_localist(data: dict) -> list[dict]:
    events = []
    items = data.get("events")
    for item in items if isinstance(items, list) else []:
        try:
            e = item.get("event") or {}
            if e.get("experience") == "virtual":
                continue
            tags = [
                f.get("name", "")
                for values in (e.get("filters") or {}).values()
                for f in values or []
            ]
            place = ", ".join(
                p for p in (e.get("room_number"), e.get("location_name")) if p
            ) or e.get("location")
            for instance in e.get("event_instances") or []:
                instance = instance.get("event_instance") or {}
                if instance.get("start") and not instance.get("all_day"):
                    events.append(
                        event(
                            e.get("title"),
                            parse_iso(instance["start"]),
                            place,
                            "",
                            e.get("description_text"),
                            tags,
                            url=e.get("localist_url") or e.get("url"),
                        )
                    )
        except BAD_ITEM:
            continue
    return events


def read_localist(base: str, day: date, days: int, quiet: bool) -> list | None:
    events: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        data = json_dict(fetch(localist_url(base, day, days, page), quiet))
        if not data or not isinstance(data.get("events"), list):
            return events if page > 1 else None
        events += from_localist(data)
        pages = data.get("page") if isinstance(data.get("page"), dict) else {}
        if page >= int(pages.get("total") or 1):
            break
    return events


# ---------- iCalendar ----------


def ics_lines(text: str) -> list[str]:
    # RFC 5545 folds long lines: a line starting with a space continues the previous one.
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def ics_text(value: str) -> str:
    return (
        value.replace("\\n", " ")
        .replace("\\N", " ")
        .replace("\\,", ",")
        .replace(r"\;", ";")
        .replace("\\\\", "\\")
    )


def ics_time(params: str, value: str, zone: tzinfo) -> datetime | None:
    # All-day entries (exhibits, deadlines) aren't something to show up to.
    if re.search(r"VALUE=DATE(?!-)", params) or len(value) == 8:
        return None
    match = re.search(r"TZID=([^;:]+)", params)
    try:
        if value.endswith("Z"):
            where = timezone.utc
        else:
            where = ZoneInfo(match.group(1).strip('"')) if match else zone
    except (ZoneInfoNotFoundError, ValueError):
        where = zone
    try:
        return datetime.strptime(value.rstrip("Z"), "%Y%m%dT%H%M%S").replace(
            tzinfo=where
        )
    except ValueError:
        return None


def weekly(first: datetime, rule: str, zone: tzinfo, window) -> list[datetime]:
    """Dates of a repeating event inside the window. Weekly rules only; others keep their first date."""
    # shortcut: FREQ=WEEKLY with BYDAY/INTERVAL/COUNT/UNTIL; EXDATE and other FREQs are ignored.
    parts = dict(p.split("=", 1) for p in rule.split(";") if "=" in p)
    if parts.get("FREQ") != "WEEKLY":
        return [first]
    interval = max(1, int(parts.get("INTERVAL") or 1))
    count = int(parts["COUNT"]) if parts.get("COUNT") else None
    until = parts.get("UNTIL", "")
    if len(until) == 8:
        until = datetime.combine(
            date(int(until[:4]), int(until[4:6]), int(until[6:])),
            time.max,
            first.tzinfo,
        )
    else:
        until = ics_time("", until, zone) if until else None
    days = sorted(
        {
            WEEKDAYS[d[-2:]]
            for d in parts.get("BYDAY", "").split(",")
            if d[-2:] in WEEKDAYS
        }
        or {first.weekday()}
    )
    low, high = window or (first, first + timedelta(weeks=52))
    monday, seen, out = first - timedelta(days=first.weekday()), 0, []
    for week in range(2000):
        week_start = monday + timedelta(weeks=week * interval)
        if week_start > high:
            break
        for offset in days:
            moment = week_start + timedelta(days=offset)
            if moment < first:
                continue
            seen += 1
            if (count and seen > count) or (until and moment > until):
                return out
            if low <= moment < high:
                out.append(moment)
    return out


def from_ics(text: str, zone: tzinfo, window=None) -> list[dict]:
    events, current = [], None
    for line in ics_lines(text):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            rule = current.pop("rrule", "")
            if current.get("start") and current.get("title"):
                try:
                    starts = (
                        weekly(current["start"], rule, zone, window)
                        if rule
                        else [current["start"]]
                    )
                except ValueError:
                    starts = [current["start"]]
                events += [event(**{**current, "start": s}) for s in starts]
            current = None
        elif current is not None and ":" in line:
            head, value = line.split(":", 1)
            name, _, params = head.partition(";")
            if name == "SUMMARY":
                current["title"] = ics_text(value)
            elif name == "DTSTART":
                current["start"] = ics_time(params, value.strip(), zone)
            elif name == "RRULE":
                current["rrule"] = value.strip()
            elif name == "LOCATION":
                current["location"] = ics_text(value)
            elif name == "DESCRIPTION":
                current["description"] = ics_text(value)
            elif name == "URL":
                current["url"] = value.strip()
            elif name == "CATEGORIES":
                current["tags"] = [t.strip() for t in ics_text(value).split(",")]
            elif name == "ORGANIZER":
                found = re.search(r"CN=\"?([^\";:]+)", params)
                current["org"] = found.group(1) if found else ""
    return events


# ---------- picking a reader ----------


def parse_feed(text: str, host: str, zone: tzinfo, window=None) -> list[dict] | None:
    """Read a feed body, or return None when it isn't a format this script knows."""
    text = text.lstrip("﻿").lstrip()
    if text.startswith("BEGIN:VCALENDAR"):
        return from_ics(text, zone, window)
    if text.startswith("<") and "campusgroups.com/rss_calendar" in text[:2000]:
        try:
            return from_campusgroups(text)
        except ElementTree.ParseError:
            return None
    data = json_dict(text) if text.startswith("{") else None
    if data and isinstance(data.get("events"), list):
        return from_localist(data)
    if data and isinstance(data.get("value"), list):
        return from_engage(data, engage_site(host))
    return None


def read_feed(url: str, start: datetime, end: datetime, zone: tzinfo) -> list[dict]:
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    host, base = parsed.netloc, f"{parsed.scheme}://{parsed.netloc}"
    day, days = start.astimezone(zone).date(), max(1, (end - start).days + 1)
    if host.endswith("campuslabs.com"):
        events = read_engage(engage_site(host), start, end, quiet=False)
    elif "/api/2/events" in parsed.path:
        events = read_localist(base, day, days, quiet=False)
    else:
        events = parse_feed(fetch(parsed.geturl()), host, zone, (start, end))
        # An events home page usually sits next to its feed: try CampusGroups,
        # then Localist, then Engage on the school's own domain.
        if events is None:
            events = parse_feed(fetch(f"{base}/rss_events", quiet=True), host, zone)
        if events is None:
            events = read_localist(base, day, days, quiet=True)
        if events is None:
            events = read_engage(base, start, end, quiet=True)
    if events is None:
        fail(
            f"Not an events feed this script can read: {url}. "
            "Read the page with the web or browser instead.",
            5,
        )
    return events


def rank(
    events: list[dict],
    start: datetime,
    end: datetime,
    interests: list[str],
    campus: str,
) -> list[dict]:
    kept, seen = [], set()
    for e in events:
        if not (start <= e["start"] < end) or not e["title"]:
            continue
        if (
            not e["location"]
            or ONLINE.search(e["location"])
            or ONLINE.search(e["title"])
        ):
            continue
        searchable = " ".join(
            [e["title"], e["description"], e["org"], " ".join(e["tags"])]
        ).lower()
        if NEVER.search(f"{searchable} {e['location']}"):
            continue
        if campus and campus.lower() not in f"{searchable} {e['location'].lower()}":
            continue
        key = (e["title"].lower(), e["start"])
        if key in seen:
            continue
        seen.add(key)
        # "board games" should match "Board Game Night": drop plural s before searching.
        e["matches"] = [
            i
            for i in interests
            if re.sub(r"(\w{3,})s\b", r"\1", i.lower()) in searchable
        ]
        e["free_food"] = e["free_food"] or bool(FREE_FOOD.search(searchable))
        e["likely_skip"] = bool(LIKELY_SKIP.search(searchable))
        kept.append(e)
    kept.sort(key=lambda e: (-len(e["matches"]), e["likely_skip"], e["start"]))
    return kept


def describe(e: dict, zone: tzinfo) -> str:
    when = e["start"].astimezone(zone)
    clock = when.strftime("%I:%M %p").lstrip("0")
    parts = [f"{when:%a %b} {when.day} {clock}", e["title"], e["location"]]
    if e["org"]:
        parts.append(f"by {e['org']}")
    notes = (["matches: " + ", ".join(e["matches"])] if e["matches"] else []) + (
        ["free food"] if e["free_food"] else []
    )
    if notes:
        parts.append("; ".join(notes))
    line = " | ".join(parts)
    if e["description"]:
        line += f"\n   {clean(e['description'], 140)}"
    if e["url"]:
        line += f"\n   {e['url']}"
    return line


def parse_zone(text: str) -> tzinfo:
    """An IANA name, or a UTC offset like -07:00 for systems without time zone data."""
    try:
        return ZoneInfo(text)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    offset = re.fullmatch(r"(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?", text.strip())
    if not offset or int(offset.group(2)) > 14:
        fail(
            f"Unknown time zone {text!r}. Use a name like America/Phoenix or an offset like UTC-07:00.",
            2,
        )
    sign = -1 if offset.group(1) == "-" else 1
    return timezone(
        sign * timedelta(hours=int(offset.group(2)), minutes=int(offset.group(3) or 0))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", help="the school's events feed or events home page")
    parser.add_argument("--today", help="the student's local date, YYYY-MM-DD")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="how many days ahead (default 7, at most 31)",
    )
    parser.add_argument(
        "--tz",
        default="UTC",
        help="the student's time zone, for example America/Phoenix or UTC-07:00",
    )
    parser.add_argument(
        "--interests",
        default="",
        help="comma-separated, for example 'climbing,board games,anime'",
    )
    parser.add_argument(
        "--campus",
        default="",
        help="keep only events mentioning this campus, for example 'Tempe'",
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--sample", action="store_true", help="read the bundled sample feed; no network"
    )
    args = parser.parse_args()

    zone = parse_zone(args.tz)
    if not 1 <= args.days <= 31:
        fail("--days must be between 1 and 31.", 2)
    try:
        day = (
            date.fromisoformat(args.today)
            if args.today
            else SAMPLE_DAY
            if args.sample
            else datetime.now(zone).date()
        )
    except ValueError:
        fail(f"--today must look like 2026-10-30, got {args.today!r}.", 2)
    start = datetime.combine(day, time(0), zone)
    end = start + timedelta(days=args.days)
    if (
        not args.sample
    ):  # the real clock is right in any time zone; drop what has started
        start = max(start, datetime.now(timezone.utc) + SOONEST)
    interests = [i.strip() for i in args.interests.split(",") if i.strip()]

    if args.sample:
        events = from_campusgroups(SAMPLE.read_text())
    elif args.url:
        events = read_feed(args.url, start, end, zone)
    else:
        fail("Give --url with the school's events feed, or --sample.", 2)

    ranked = rank(events, start, end, interests, args.campus)
    last = (end - timedelta(days=1)).date()
    if not ranked:
        fail(f"No in-person events between {day} and {last}.", 3)
    shown = ranked[: args.limit]
    print(f"{len(ranked)} in-person events, {day} to {last}. Top {len(shown)}:")
    for number, e in enumerate(shown, 1):
        print(f"{number}. {describe(e, zone)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

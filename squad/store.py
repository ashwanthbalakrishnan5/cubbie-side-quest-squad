"""All state in one JSON file, written atomically.

shortcut: one file for every squad, fine for a handful of servers; move to SQLite if it ever runs for many.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Iterable
from pathlib import Path

from .models import Member, Plan, Squad


class Store:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self._members: dict[str, Member] = {}
        self._squads: dict[str, Squad] = {}
        self._plans: dict[str, Plan] = {}

    async def load(self) -> None:
        if not self.path.exists():
            return
        doc = json.loads(self.path.read_text())
        self._members = {
            k: Member.model_validate(v) for k, v in doc.get("members", {}).items()
        }
        self._squads = {
            k: Squad.model_validate(v) for k, v in doc.get("squads", {}).items()
        }
        self._plans = {
            k: Plan.model_validate(v) for k, v in doc.get("plans", {}).items()
        }

    def member(self, member_id: str) -> Member | None:
        return self._members.get(member_id)

    def members(self, ids: Iterable[str]) -> list[Member]:
        return [self._members[i] for i in ids if i in self._members]

    def squad(self, channel_id: str) -> Squad | None:
        return self._squads.get(channel_id)

    def squads(self) -> list[Squad]:
        return list(self._squads.values())

    def plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def plans(self, *statuses: str) -> list[Plan]:
        return [p for p in self._plans.values() if not statuses or p.status in statuses]

    async def put_member(self, m: Member) -> None:
        self._members[m.id] = m
        await self._save()

    async def put_squad(self, s: Squad) -> None:
        self._squads[s.channel_id] = s
        await self._save()

    async def put_plan(self, p: Plan) -> None:
        self._plans[p.id] = p
        await self._save()

    async def delete_member(self, member_id: str) -> None:
        self._members.pop(member_id, None)
        for squad in self._squads.values():
            if member_id in squad.member_ids:
                squad.member_ids = [i for i in squad.member_ids if i != member_id]
        await self._save()

    async def _save(self) -> None:
        async with self._lock:
            doc = {
                "members": {
                    k: v.model_dump(mode="json") for k, v in self._members.items()
                },
                "squads": {
                    k: v.model_dump(mode="json") for k, v in self._squads.items()
                },
                "plans": {k: v.model_dump(mode="json") for k, v in self._plans.items()},
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, indent=1))
            os.replace(tmp, self.path)

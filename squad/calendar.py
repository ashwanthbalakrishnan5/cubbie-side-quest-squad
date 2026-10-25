"""Google Calendar busy times through Composio Connect Links.

The Composio SDK is synchronous; callers wrap these calls in asyncio.to_thread.
Only busy start/end times are read; event titles are never requested or stored.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from composio import Composio
from composio.exceptions import ComposioMultipleConnectedAccountsError

from .models import BusyBlock

log = logging.getLogger(__name__)


def composio_user_id(member_id: str) -> str:
    return f"discord:{member_id}"


class CalendarLinker:
    def __init__(
        self, composio: Composio, auth_config_id: str, callback_url: str
    ) -> None:
        self.composio = composio
        self.auth_config_id = auth_config_id
        self.callback_url = callback_url

    def connect_url(self, member_id: str) -> str | None:
        try:
            request = self.composio.connected_accounts.link(
                composio_user_id(member_id),
                self.auth_config_id,
                callback_url=self.callback_url,
            )
        except ComposioMultipleConnectedAccountsError:
            return None  # already connected
        return request.redirect_url

    def is_connected(self, member_id: str) -> bool:
        accounts = self.composio.connected_accounts.list(
            user_ids=[composio_user_id(member_id)],
            toolkit_slugs=["googlecalendar"],
            statuses=["ACTIVE"],
        )
        return len(accounts.items) >= 1

    def busy_blocks(
        self, member_id: str, start: datetime, end: datetime, tz: ZoneInfo
    ) -> list[BusyBlock] | None:
        try:
            if not self.is_connected(member_id):
                return None
            result = self.composio.tools.execute(
                "GOOGLECALENDAR_FIND_FREE_SLOTS",
                {
                    "items": ["primary"],
                    "time_min": start.isoformat(),
                    "time_max": end.isoformat(),
                    "timezone": tz.key,
                },
                user_id=composio_user_id(member_id),
                dangerously_skip_version_check=True,
            )
            if not result.get("successful"):
                log.warning("calendar lookup failed for a member")
                return None
            return [
                BusyBlock(start=b["start"], end=b["end"])
                for calendar in result["data"]["calendars"].values()
                for b in calendar.get("busy", [])
            ]
        # any SDK, network or shape problem means "unknown", never a crash
        except Exception as error:  # noqa: BLE001
            log.warning("calendar lookup error: %s", type(error).__name__)
            return None

    def disconnect(self, member_id: str) -> None:
        accounts = self.composio.connected_accounts.list(
            user_ids=[composio_user_id(member_id)]
        )
        for account in accounts.items:
            self.composio.connected_accounts.delete(account.id)

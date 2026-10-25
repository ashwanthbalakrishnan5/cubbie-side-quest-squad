"""Settings from the environment (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    anthropic_api_key: str
    gemini_api_key: str
    composio_api_key: str = ""
    composio_calendar_auth_config: str = "ac_aze6I2N0XYM_"
    public_url: str = "http://localhost:8090"
    web_port: int = 8090
    wa_voice_url: str = "http://127.0.0.1:8091"
    data_dir: Path = Path("data")
    tz: ZoneInfo = field(default_factory=lambda: ZoneInfo("America/Phoenix"))
    events_url: str = "https://sundevilcentral.eoss.asu.edu/rss_events"
    campus: str = "Tempe Campus"
    dev_channel_id: int = 1563800077368295476
    demo_fast: bool = False
    demo_phone: str = ""  # the presenter's WhatsApp number for /squad demo

    @property
    def confirm_timeout_s(self) -> int:
        return 60 if self.demo_fast else 600

    @property
    def nudge_after_s(self) -> int:
        return 60 if self.demo_fast else 1800

    @property
    def persona_vote_delays_s(self) -> tuple[int, int, int, int]:
        return (5, 9, 14, 20) if self.demo_fast else (60, 240, 600, 900)


def load_settings() -> Settings:
    load_dotenv()
    env = os.environ.get
    return Settings(
        discord_token=env("DISCORD_TOKEN", ""),
        anthropic_api_key=env("ANTHROPIC_API_KEY", ""),
        gemini_api_key=env("GEMINI_API_KEY", ""),
        composio_api_key=env("COMPOSIO_API_KEY", ""),
        composio_calendar_auth_config=env(
            "COMPOSIO_CALENDAR_AUTH_CONFIG", "ac_aze6I2N0XYM_"
        )
        or "ac_aze6I2N0XYM_",
        public_url=env("PUBLIC_URL", "http://localhost:8090").rstrip("/"),
        web_port=int(env("WEB_PORT", "8090")),
        wa_voice_url=env("WA_VOICE_URL", "http://127.0.0.1:8091").rstrip("/"),
        data_dir=Path(env("DATA_DIR", "data")),
        dev_channel_id=int(env("DEV_CHANNEL_ID") or 1563800077368295476),
        demo_fast=env("DEMO_FAST", "0") not in ("", "0", "false", "False"),
        demo_phone=env("DEMO_PHONE", "").strip(),
    )

"""Entry point: `python -m squad` runs the bot and web server; `--check` validates setup offline."""

from __future__ import annotations

import asyncio
import importlib
import logging
import pkgutil
import sys

from aiohttp import web
from anthropic import AsyncAnthropic
from composio import Composio

import squad

from .bot import SquadBot
from .calendar import CalendarLinker
from .config import Settings, load_settings
from .llm import LLM
from .store import Store
from .web import make_app

REQUIRED = ("discord_token", "anthropic_api_key", "gemini_api_key")


def import_all() -> None:
    for mod in pkgutil.walk_packages(squad.__path__, "squad."):
        if mod.name != "squad.__main__":
            importlib.import_module(mod.name)


async def run(settings: Settings) -> None:
    calendar = None
    if settings.composio_api_key:
        calendar = CalendarLinker(
            Composio(api_key=settings.composio_api_key),
            settings.composio_calendar_auth_config,
            f"{settings.public_url}/calendar/done",
        )
    bot = SquadBot(
        settings,
        Store(settings.data_dir / "squad.json"),
        LLM(AsyncAnthropic(api_key=settings.anthropic_api_key)),
        calendar,
    )
    runner = web.AppRunner(make_app(settings))
    await runner.setup()
    # All interfaces: the Caddy container reaches us through host.docker.internal.
    await web.TCPSite(runner, port=settings.web_port).start()
    try:
        async with bot:
            await bot.start(settings.discord_token)
    finally:
        await runner.cleanup()


def main() -> int:
    settings = load_settings()
    if missing := [k.upper() for k in REQUIRED if not getattr(settings, k)]:
        print(f"missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1
    if "--check" in sys.argv[1:]:
        import_all()
        print("ok")
        return 0
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    asyncio.run(run(settings))
    return 0


if __name__ == "__main__":
    sys.exit(main())

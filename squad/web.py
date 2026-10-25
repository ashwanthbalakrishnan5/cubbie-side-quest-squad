"""Small web server: project site, health check, and the page Composio returns to after calendar sign-in."""

from __future__ import annotations

from pathlib import Path

from aiohttp import web

from .config import Settings

SITE = Path(__file__).parent / "site" / "index.html"

DONE_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Calendar connected</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#faf6f1;color:#2b1d22;
font:18px/1.5 system-ui,sans-serif;text-align:center;padding:16px}
@media (prefers-color-scheme:dark){body{background:#1c1417;color:#f4ece6}}</style></head>
<body><main><p style="font-size:48px;margin:0">✨</p><h1>Calendar connected</h1>
<p>You can close this tab and head back to Discord.<br>I only ever look at when you're busy, never what it is.</p>
</main></body></html>"""


def make_app(settings: Settings) -> web.Application:
    async def index(_: web.Request) -> web.Response:
        return web.Response(text=SITE.read_text(), content_type="text/html")

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async def calendar_done(_: web.Request) -> web.Response:
        return web.Response(text=DONE_PAGE, content_type="text/html")

    app = web.Application()
    app["settings"] = settings
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/calendar/done", calendar_done)
    # demo video and poster live outside git, in data/media on the server
    media = settings.data_dir / "media"
    media.mkdir(parents=True, exist_ok=True)
    app.router.add_static("/media/", media)
    return app

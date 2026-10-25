import pytest
from aiohttp.test_utils import TestClient, TestServer

from squad.config import Settings
from squad.web import make_app


@pytest.fixture
async def client():
    app = make_app(
        Settings(discord_token="x", anthropic_api_key="x", gemini_api_key="x")
    )
    async with TestClient(TestServer(app)) as c:
        yield c


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status == 200
    assert await resp.json() == {"ok": True}


async def test_calendar_done_page(client):
    resp = await client.get("/calendar/done")
    assert resp.status == 200
    assert "Calendar connected" in await resp.text()


async def test_index_has_install_link(client):
    resp = await client.get("/")
    text = await resp.text()
    assert "discord.com/oauth2/authorize?client_id=1563800334231670835" in text
    assert "Side Quests: Squad Mode" in text

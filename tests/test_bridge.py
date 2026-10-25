import asyncio
import json
from datetime import datetime

import pytest
from aiohttp import WSMsgType, web
from aiohttp.test_utils import TestServer
from google.genai import types

from squad.config import Settings
from squad.models import Plan
from squad.voice import bridge
from tests.fakes import TZ, make_event


class FakeSession:
    def __init__(self, turns):
        self.turns = turns
        self.audio_in: list[bytes] = []
        self.tool_responses: list = []

    async def send_realtime_input(self, *, audio):
        self.audio_in.append(audio.data)

    async def send_tool_response(self, *, function_responses):
        self.tool_responses.append(function_responses)

    async def receive(self):
        if not self.turns:
            await asyncio.Event().wait()  # a live session that never speaks again
        for msg in self.turns.pop(0):
            yield msg


class FakeGenai:
    def __init__(self, session, on_close=None):
        self.session = session
        self.on_close = on_close
        self.connects: list[dict] = []
        self.aio = self
        self.live = self

    def connect(self, *, model, config):
        self.connects.append({"model": model, "config": config})
        fake = self

        class _CM:
            async def __aenter__(self):
                return fake.session

            async def __aexit__(self, *exc):
                if fake.on_close:
                    await fake.on_close()
                return False

        return _CM()


def _audio_msg(n: int) -> types.LiveServerMessage:
    blob = types.Blob(data=b"\x00\x01" * n, mime_type="audio/pcm;rate=24000")
    content = types.Content(parts=[types.Part(inline_data=blob)])
    return types.LiveServerMessage(
        server_content=types.LiveServerContent(model_turn=content)
    )


def _tool_msg(answer: str) -> types.LiveServerMessage:
    call = types.FunctionCall(id="f1", name="record_answer", args={"answer": answer})
    return types.LiveServerMessage(
        tool_call=types.LiveServerToolCall(function_calls=[call])
    )


DONE = types.LiveServerMessage(
    server_content=types.LiveServerContent(turn_complete=True)
)


async def _sidecar(call_status=200, answer=True):
    seen = {"calls": [], "hangup": False, "audio": b""}

    async def call(request):
        seen["calls"].append(await request.json())
        if call_status != 200:
            return web.json_response({"error": "busy"}, status=call_status)
        return web.json_response({"call_id": "c1"})

    async def audio(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        if answer:
            await ws.send_str(json.dumps({"event": "answered"}))
            await ws.send_bytes(b"\x00\x00" * 320)
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                seen["audio"] += msg.data
            elif msg.type == WSMsgType.TEXT and json.loads(msg.data) == {
                "cmd": "hangup"
            }:
                seen["hangup"] = True
                break
        return ws

    app = web.Application()
    app.router.add_post("/call", call)
    app.router.add_get("/audio/{call_id}", audio)
    server = TestServer(app)
    await server.start_server()
    return server, seen


def _settings(server) -> Settings:
    return Settings(
        discord_token="",
        anthropic_api_key="",
        gemini_api_key="test",
        wa_voice_url=str(server.make_url("")).rstrip("/"),
    )


def _plan() -> Plan:
    return Plan(
        id="p1",
        channel_id="c",
        event=make_event(),
        headline="Open mic",
        why="music",
        created_at=datetime(2026, 10, 25, 12, tzinfo=TZ),
    )


async def test_nudge_call_records_answer(monkeypatch):
    monkeypatch.setattr(bridge, "GOODBYE_S", 0)
    server, seen = await _sidecar()
    # Real Live order: tool_call + turn_complete, then a goodbye audio turn after our reply.
    session = FakeSession(
        [[_audio_msg(2400), _tool_msg("yes"), DONE], [_audio_msg(2400), DONE]]
    )
    hangup_at_close: list[bool] = []

    async def on_close():  # give the sidecar up to 1 s to read a hangup already sent
        for _ in range(100):
            if seen["hangup"]:
                break
            await asyncio.sleep(0.01)
        hangup_at_close.append(seen["hangup"])

    genai = FakeGenai(session, on_close=on_close)
    try:
        out = await bridge.nudge_call(
            _settings(server),
            "+14805550123",
            "Sam",
            _plan(),
            ["Ana"],
            genai_client=genai,
        )
    finally:
        await server.close()
    assert out.answered is True
    assert out.answer == "yes"
    assert seen["hangup"] is True
    assert seen["calls"] == [{"phone": "+14805550123"}]
    # both chunks (incl. the goodbye) reached the sidecar before the hangup, 24 kHz -> 16 kHz
    assert len(seen["audio"]) == 2 * 1600 * 2
    assert hangup_at_close == [True]  # hung up before waiting on the Live session close
    (resp,) = session.tool_responses
    assert resp.response == {"result": "ok"} and resp.id == "f1"
    (conn,) = genai.connects
    assert conn["model"] == "gemini-3.8-live"
    instr = conn["config"]["system_instruction"]
    assert "You're calling Sam" in instr and "Already going: Ana." in instr
    assert conn["config"]["tools"] == [
        {"function_declarations": [bridge.RECORD_ANSWER]}
    ]


async def test_nudge_call_sidecar_busy_returns_unanswered():
    server, seen = await _sidecar(call_status=409)
    genai = FakeGenai(FakeSession([]))
    try:
        out = await bridge.nudge_call(
            _settings(server), "+14805550123", "Sam", _plan(), [], genai_client=genai
        )
    finally:
        await server.close()
    assert out == bridge.CallOutcome(answered=False)
    assert genai.connects == []
    assert seen["calls"] == [{"phone": "+14805550123"}]


async def test_nudge_call_times_out(monkeypatch):
    monkeypatch.setattr(bridge, "CALL_LIMIT_S", 0.2)
    server, seen = await _sidecar(answer=False)
    try:
        out = await asyncio.wait_for(
            bridge.nudge_call(
                _settings(server),
                "+14805550123",
                "Sam",
                _plan(),
                [],
                genai_client=FakeGenai(FakeSession([])),
            ),
            5,
        )
    finally:
        await server.close()
    assert out.answered is False
    assert out.answer is None
    assert seen["hangup"] is True


@pytest.fixture(autouse=True)
def _no_real_genai(monkeypatch):
    monkeypatch.setattr(bridge.genai, "Client", None)

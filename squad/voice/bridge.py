"""Bridge a wa-voice sidecar call to a Gemini Live session and record the answer."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from typing import Literal

import aiohttp
from google import genai
from google.genai import types
from pydantic import BaseModel

from squad.config import Settings
from squad.models import Plan
from squad.voice.resample import pcm16_24k_to_16k

log = logging.getLogger(__name__)

MODEL = "gemini-3.8-live"
CALL_LIMIT_S = 90.0
GOODBYE_S = 3.0

VOICE_SYSTEM = (
    "You're calling {name} for their friend group's Side Quests squad. They haven't "
    "answered the poll yet. The plan: {title}, {when}, at {location}. Already going: "
    "{going}. Say hi, say it's the squad bot calling, give the plan in one sentence, "
    "and ask if they're in. Be warm and brief, like a friend, never pushy. If they say "
    "yes, maybe or no, call record_answer. If they give a reason, include it. Then say "
    "a short goodbye. Keep the whole call under a minute."
)

RECORD_ANSWER = {
    "name": "record_answer",
    "description": "Save their answer to the poll",
    "parameters": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "enum": ["yes", "maybe", "no"]},
            "reason": {"type": "string"},
        },
        "required": ["answer"],
    },
}


class CallOutcome(BaseModel):
    answered: bool
    answer: Literal["yes", "maybe", "no"] | None = None
    reason: str = ""
    seconds: float = 0.0


async def nudge_call(
    settings: Settings,
    phone: str,
    name: str,
    plan: Plan,
    going_names: list[str],
    *,
    genai_client=None,
    ws_connect=None,
) -> CallOutcome:
    """Ring `phone` through the sidecar and let Gemini ask about the plan. Never raises."""
    base = settings.wa_voice_url
    try:
        async with aiohttp.ClientSession() as http:
            async with http.post(f"{base}/call", json={"phone": phone}) as r:
                if r.status != 200:
                    return CallOutcome(answered=False)
                call_id = (await r.json())["call_id"]
            ws = await (ws_connect or http.ws_connect)(f"{base}/audio/{call_id}")
            try:
                return await _bridge(
                    settings, ws, name, plan, going_names, genai_client
                )
            finally:
                await _hangup(ws)
    except Exception as e:  # noqa: BLE001 - a failed nudge must never crash a flow
        log.warning("voice call failed: %s", type(e).__name__)
        return CallOutcome(answered=False)


async def _hangup(ws) -> None:
    if ws.closed:
        return
    with contextlib.suppress(Exception):
        await ws.send_str(json.dumps({"cmd": "hangup"}))
        await ws.close()


async def _bridge(settings, ws, name, plan, going_names, genai_client) -> CallOutcome:
    ev = plan.event
    when = ev.start.astimezone(settings.tz).strftime("%A %-I:%M %p")
    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": VOICE_SYSTEM.format(
            name=name,
            title=ev.title,
            when=when,
            location=ev.location,
            going=", ".join(going_names) or "nobody yet",
        ),
        "tools": [{"function_declarations": [RECORD_ANSWER]}],
    }
    client = genai_client or genai.Client(api_key=settings.gemini_api_key)
    state: dict = {"answered": False, "answer": None, "reason": ""}
    started = time.monotonic()
    ended: float | None = None

    async def callee_to_model(session) -> None:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.BINARY:
                blob = types.Blob(data=msg.data, mime_type="audio/pcm;rate=16000")
                await session.send_realtime_input(audio=blob)
            elif msg.type == aiohttp.WSMsgType.TEXT:
                event = json.loads(msg.data).get("event")
                if event == "answered":
                    state["answered"] = True
                elif event == "ended":
                    return

    async def model_to_callee(session) -> None:
        carry = b""
        responded = goodbye = False  # goodbye: model audio after our tool response
        while True:
            got = False
            async for resp in session.receive():
                got = True
                if resp.data:
                    out, carry = pcm16_24k_to_16k(resp.data, carry)
                    await ws.send_bytes(out)
                    goodbye |= responded
                if resp.tool_call:
                    for fc in resp.tool_call.function_calls or []:
                        if fc.name != "record_answer":
                            continue
                        args = fc.args or {}
                        if args.get("answer") in ("yes", "maybe", "no"):
                            state.update(
                                answered=True,
                                answer=args["answer"],
                                reason=str(args.get("reason") or ""),
                            )
                        await session.send_tool_response(
                            function_responses=types.FunctionResponse(
                                id=fc.id, name=fc.name, response={"result": "ok"}
                            )
                        )
                        responded = True
                sc = resp.server_content
                # the tool-call turn completes silently; end on the goodbye turn
                if goodbye and state["answer"] and sc and sc.turn_complete:
                    await asyncio.sleep(GOODBYE_S)  # let the goodbye play out
                    return
            if not got:  # session closed
                return

    with contextlib.suppress(TimeoutError):
        async with asyncio.timeout(CALL_LIMIT_S):
            async with client.aio.live.connect(model=MODEL, config=config) as session:
                tasks = [
                    asyncio.create_task(callee_to_model(session)),
                    asyncio.create_task(model_to_callee(session)),
                ]
                try:
                    done, _ = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                finally:
                    for t in tasks:
                        t.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    ended = time.monotonic()
                    await _hangup(ws)  # the Live close below can take ~10 s
                for t in done:  # keep an answer already recorded if a pump broke
                    if t.exception():
                        log.warning(
                            "voice pump failed: %s", type(t.exception()).__name__
                        )
    return CallOutcome(**state, seconds=round((ended or time.monotonic()) - started, 1))

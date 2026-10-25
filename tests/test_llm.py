from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from pydantic import BaseModel

from squad.llm import LLM, LLMError


class Out(BaseModel):
    x: int


class StubMessages:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.kwargs = result, error, None

    async def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.result


def stub_client(**kw):
    return SimpleNamespace(messages=StubMessages(**kw))


async def test_ok_returns_parsed_and_sends_effort():
    client = stub_client(
        result=SimpleNamespace(stop_reason="end_turn", parsed_output=Out(x=1))
    )
    out = await LLM(client).parse(system="s", user="u", schema=Out, effort="low")
    assert out == Out(x=1)
    kw = client.messages.kwargs
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_format"] is Out
    assert kw["output_config"] == {"effort": "low"}
    assert "temperature" not in kw and "thinking" not in kw


async def test_refusal_raises():
    client = stub_client(
        result=SimpleNamespace(stop_reason="refusal", parsed_output=None)
    )
    with pytest.raises(LLMError):
        await LLM(client).parse(system="s", user="u", schema=Out, effort="low")


async def test_none_output_raises():
    client = stub_client(
        result=SimpleNamespace(stop_reason="end_turn", parsed_output=None)
    )
    with pytest.raises(LLMError):
        await LLM(client).parse(system="s", user="u", schema=Out, effort="low")


async def test_api_error_raises():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    client = stub_client(error=anthropic.APIConnectionError(request=request))
    with pytest.raises(LLMError):
        await LLM(client).parse(system="s", user="u", schema=Out, effort="medium")

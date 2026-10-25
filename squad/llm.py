"""Claude wrapper: one structured-output call, every failure becomes LLMError."""

from __future__ import annotations

import logging
from typing import Literal, TypeVar

import anthropic
import pydantic

log = logging.getLogger(__name__)
T = TypeVar("T")


class LLMError(Exception):
    """Claude failed, refused, or returned nothing usable."""


class LLM:
    def __init__(
        self, client: anthropic.AsyncAnthropic, model: str = "claude-opus-5-5"
    ) -> None:
        self.client = client
        self.model = model

    async def parse(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        effort: Literal["low", "medium"],
    ) -> T:
        try:
            msg = await self.client.messages.parse(
                model=self.model,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
                output_config={"effort": effort},
                extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
                extra_body={"fallbacks": "default"},
            )
        except (anthropic.APIError, pydantic.ValidationError) as e:
            log.warning("claude call failed: %s", type(e).__name__)
            raise LLMError(type(e).__name__) from e
        log.info("claude %s stop_reason=%s", schema.__name__, msg.stop_reason)
        if msg.stop_reason in ("refusal", "max_tokens"):
            raise LLMError(f"stop_reason={msg.stop_reason}")
        if msg.parsed_output is None:
            raise LLMError("no parsed output")
        return msg.parsed_output

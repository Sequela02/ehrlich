from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_DELAY = 1.0


@dataclass(frozen=True)
class MessageResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int


class AnthropicClientAdapter:
    def __init__(
        self,
        model: str = "claude-opus-4-6",
        max_tokens: int = 16384,
        api_key: str | None = None,
    ) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key or None)
        self._model = model
        self._max_tokens = max_tokens

    @property
    def model(self) -> str:
        return self._model

    async def create_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> MessageResponse:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=system,
                    messages=messages,  # type: ignore[arg-type]
                    tools=tools,  # type: ignore[arg-type]
                )
                content = _parse_content_blocks(response.content)
                return MessageResponse(
                    content=content,
                    stop_reason=response.stop_reason or "end_turn",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            except (anthropic.RateLimitError, anthropic.APITimeoutError) as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "Anthropic API %s (attempt %d/%d), retrying in %.1fs",
                    type(e).__name__,
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
            except anthropic.APIError as e:
                logger.error("Anthropic API error: %s", e)
                raise

        raise last_error  # type: ignore[misc]


def _parse_content_blocks(blocks: Any) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for block in blocks:
        if block.type == "text":
            parsed.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            parsed.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
    return parsed

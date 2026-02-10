from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import anthropic

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MessageResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int


class AnthropicClientAdapter:
    def __init__(self, model: str = "claude-sonnet-4-5-20250929", max_tokens: int = 16384) -> None:
        self._client = anthropic.AsyncAnthropic()
        self._model = model
        self._max_tokens = max_tokens

    async def create_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> MessageResponse:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                messages=messages,  # type: ignore[arg-type]
                tools=tools,  # type: ignore[arg-type]
            )
        except anthropic.RateLimitError:
            logger.warning("Rate limited by Anthropic API, raising")
            raise
        except anthropic.APITimeoutError:
            logger.warning("Anthropic API timeout, raising")
            raise
        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            raise

        content = _parse_content_blocks(response.content)
        return MessageResponse(
            content=content,
            stop_reason=response.stop_reason or "end_turn",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


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

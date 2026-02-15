from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import anthropic

logger = logging.getLogger(__name__)


def _sanitize_error(msg: str) -> str:
    """Remove Anthropic API keys from error messages."""
    return re.sub(r"sk-ant-[A-Za-z0-9_-]+", "[REDACTED]", msg)


_MAX_RETRIES = 3
_BASE_DELAY = 1.0


@dataclass(frozen=True)
class MessageResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_write_input_tokens: int = 0


class AnthropicClientAdapter:
    def __init__(
        self,
        model: str = "claude-opus-4-6",
        max_tokens: int = 16384,
        api_key: str | None = None,
        effort: str | None = None,
        thinking: dict[str, Any] | None = None,
    ) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key or None)
        self._model = model
        self._max_tokens = max_tokens
        self._effort = effort
        self._thinking = thinking

    @property
    def model(self) -> str:
        return self._model

    async def create_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
        output_config: dict[str, Any] | None = None,
    ) -> MessageResponse:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                kwargs = self._build_kwargs(system, messages, tools, tool_choice, output_config)
                response = await self._client.messages.create(**kwargs)
                content = _parse_content_blocks(response.content)
                usage = response.usage
                cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
                cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0

                return MessageResponse(
                    content=content,
                    stop_reason=response.stop_reason or "end_turn",
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cache_read_input_tokens=cache_read,
                    cache_write_input_tokens=cache_write,
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
                logger.error("Anthropic API error: %s", _sanitize_error(str(e)))
                raise

        raise last_error  # type: ignore[misc]

    async def stream_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        tool_choice: dict[str, Any] | None = None,
        output_config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                kwargs = self._build_kwargs(system, messages, tools, tool_choice, output_config)
                async with self._client.messages.stream(**kwargs) as stream:
                    async for event in stream:
                        if event.type == "thinking":
                            yield {"type": "thinking", "text": event.thinking}
                        elif event.type == "text":
                            yield {"type": "text", "text": event.text}

                    final = await stream.get_final_message()
                    usage = final.usage
                    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
                    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0

                    yield {
                        "type": "result",
                        "response": MessageResponse(
                            content=_parse_content_blocks(final.content),
                            stop_reason=final.stop_reason or "end_turn",
                            input_tokens=usage.input_tokens,
                            output_tokens=usage.output_tokens,
                            cache_read_input_tokens=cache_read,
                            cache_write_input_tokens=cache_write,
                        ),
                    }
                    return
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
                logger.error("Anthropic API error: %s", _sanitize_error(str(e)))
                raise

        raise last_error  # type: ignore[misc]

    def _build_kwargs(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: dict[str, Any] | None = None,
        output_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cached_tools = tools
        if tools:
            cached_tools = [
                *tools[:-1],
                {**tools[-1], "cache_control": {"type": "ephemeral"}},
            ]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
            "tools": cached_tools,
        }

        merged_output: dict[str, Any] = {}
        if self._effort is not None:
            merged_output["effort"] = self._effort
        if output_config is not None:
            merged_output.update(output_config)
        if merged_output:
            kwargs["output_config"] = merged_output

        if self._thinking is not None:
            kwargs["thinking"] = self._thinking

        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        return kwargs


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
        elif block.type == "thinking":
            parsed.append({"type": "thinking", "thinking": block.thinking})
    return parsed

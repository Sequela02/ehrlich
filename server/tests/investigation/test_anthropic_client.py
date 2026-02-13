from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ehrlich.investigation.infrastructure.anthropic_client import (
    AnthropicClientAdapter,
    MessageResponse,
)

# -- Fakes for streaming --


class FakeStreamEvent:
    def __init__(self, type: str, text: str = "", thinking: str = "") -> None:
        self.type = type
        self.text = text
        self.thinking = thinking


class FakeUsage:
    input_tokens = 200
    output_tokens = 100
    cache_read_input_tokens = 50
    cache_creation_input_tokens = 30


class FakeFinalMessage:
    content = [MagicMock(type="text", text="result text")]
    stop_reason = "end_turn"
    usage = FakeUsage()


class FakeStream:
    def __init__(
        self,
        events: list[FakeStreamEvent],
        final_message: Any = None,
    ) -> None:
        self._events = events
        self._final = final_message or FakeFinalMessage()

    def __aiter__(self) -> FakeStream:
        self._iter = iter(self._events)
        return self

    async def __anext__(self) -> FakeStreamEvent:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None

    async def get_final_message(self) -> Any:
        return self._final


class FakeStreamManager:
    def __init__(self, stream: FakeStream) -> None:
        self._stream = stream

    async def __aenter__(self) -> FakeStream:
        return self._stream

    async def __aexit__(self, *args: Any) -> None:
        pass


# -- Fixtures --


def _make_adapter() -> AnthropicClientAdapter:
    adapter = AnthropicClientAdapter(api_key="test-key")
    return adapter


def _make_response(
    text: str = "hello",
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> MagicMock:
    block = MagicMock(type="text", text=text)
    usage = MagicMock(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=10,
        cache_creation_input_tokens=5,
    )
    resp = MagicMock(content=[block], stop_reason=stop_reason, usage=usage)
    return resp


# -- create_message tests --


@pytest.mark.asyncio
async def test_output_config_passed_to_create_message() -> None:
    adapter = _make_adapter()
    adapter._client.messages.create = AsyncMock(return_value=_make_response())

    config = {"type": "json_schema", "json_schema": {"name": "test"}}
    await adapter.create_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
        output_config=config,
    )

    call_kwargs = adapter._client.messages.create.call_args[1]
    assert call_kwargs["output_config"] == config


@pytest.mark.asyncio
async def test_output_config_omitted_when_none() -> None:
    adapter = _make_adapter()
    adapter._client.messages.create = AsyncMock(return_value=_make_response())

    await adapter.create_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
    )

    call_kwargs = adapter._client.messages.create.call_args[1]
    assert "output_config" not in call_kwargs


# -- stream_message tests --


@pytest.mark.asyncio
async def test_stream_yields_thinking_events() -> None:
    adapter = _make_adapter()
    events = [
        FakeStreamEvent("thinking", thinking="step 1"),
        FakeStreamEvent("thinking", thinking="step 2"),
    ]
    stream = FakeStream(events)
    adapter._client.messages.stream = MagicMock(return_value=FakeStreamManager(stream))

    yielded = []
    async for chunk in adapter.stream_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
    ):
        yielded.append(chunk)

    thinking = [c for c in yielded if c["type"] == "thinking"]
    assert len(thinking) == 2
    assert thinking[0]["text"] == "step 1"
    assert thinking[1]["text"] == "step 2"


@pytest.mark.asyncio
async def test_stream_yields_text_events() -> None:
    adapter = _make_adapter()
    events = [FakeStreamEvent("text", "hello "), FakeStreamEvent("text", "world")]
    stream = FakeStream(events)
    adapter._client.messages.stream = MagicMock(return_value=FakeStreamManager(stream))

    yielded = []
    async for chunk in adapter.stream_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
    ):
        yielded.append(chunk)

    text = [c for c in yielded if c["type"] == "text"]
    assert len(text) == 2
    assert text[0]["text"] == "hello "
    assert text[1]["text"] == "world"


@pytest.mark.asyncio
async def test_stream_yields_result_with_usage() -> None:
    adapter = _make_adapter()
    events = [FakeStreamEvent("text", "hi")]
    stream = FakeStream(events)
    adapter._client.messages.stream = MagicMock(return_value=FakeStreamManager(stream))

    yielded = []
    async for chunk in adapter.stream_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
    ):
        yielded.append(chunk)

    result = [c for c in yielded if c["type"] == "result"]
    assert len(result) == 1
    resp: MessageResponse = result[0]["response"]
    assert resp.input_tokens == 200
    assert resp.output_tokens == 100
    assert resp.cache_read_input_tokens == 50
    assert resp.cache_write_input_tokens == 30
    assert resp.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_output_config_passed_to_stream() -> None:
    adapter = _make_adapter()
    events = [FakeStreamEvent("text", "hi")]
    stream = FakeStream(events)
    adapter._client.messages.stream = MagicMock(return_value=FakeStreamManager(stream))

    config = {"type": "json_schema", "json_schema": {"name": "test"}}
    async for _ in adapter.stream_message(
        system="sys",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"name": "t", "input_schema": {}}],
        output_config=config,
    ):
        pass

    call_kwargs = adapter._client.messages.stream.call_args[1]
    assert call_kwargs["output_config"] == config

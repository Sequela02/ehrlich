from typing import Any


class AnthropicClientAdapter:
    async def create_message(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise NotImplementedError

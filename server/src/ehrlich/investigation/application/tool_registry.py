from collections.abc import Callable
from typing import Any

ToolFunction = Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFunction] = {}

    def register(self, name: str, func: ToolFunction) -> None:
        self._tools[name] = func

    def get(self, name: str) -> ToolFunction | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

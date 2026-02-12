from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MCPServerConfig:
    """Configuration for an external MCP server connection."""

    name: str
    transport: str  # "stdio" | "sse" | "streamable_http"
    command: str = ""
    args: tuple[str, ...] = ()
    env: dict[str, str] | None = None
    url: str = ""
    tags: frozenset[str] = frozenset()
    enabled: bool = True
    tool_prefix: bool = True

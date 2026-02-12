from __future__ import annotations

import json
import logging
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

if TYPE_CHECKING:
    from ehrlich.investigation.domain.mcp_config import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPBridge:
    """Manages connections to external MCP servers and exposes their tools."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._configs: dict[str, MCPServerConfig] = {}
        self._tool_map: dict[str, str] = {}  # prefixed_name -> server_name

    async def connect(self, configs: list[MCPServerConfig]) -> None:
        """Start all enabled MCP servers and initialize sessions."""
        for config in configs:
            if not config.enabled:
                continue
            try:
                session = await self._connect_one(config)
                self._sessions[config.name] = session
                self._configs[config.name] = config
                await self._index_tools(config)
                logger.info("MCP server '%s' connected (%s)", config.name, config.transport)
            except Exception:
                logger.exception("Failed to connect MCP server '%s'", config.name)

    async def disconnect(self) -> None:
        """Gracefully close all sessions and subprocesses."""
        await self._stack.aclose()
        self._sessions.clear()
        self._configs.clear()
        self._tool_map.clear()

    @property
    def connected_servers(self) -> list[str]:
        return list(self._sessions.keys())

    async def list_tools(self, server_name: str | None = None) -> list[dict[str, Any]]:
        """Return Anthropic-format tool schemas from connected MCP servers."""
        tools: list[dict[str, Any]] = []
        targets = (
            [(server_name, self._sessions[server_name])]
            if server_name and server_name in self._sessions
            else list(self._sessions.items())
        )
        for name, session in targets:
            config = self._configs[name]
            result = await session.list_tools()
            for tool in result.tools:
                tool_name = f"{name}:{tool.name}" if config.tool_prefix else tool.name
                schema = tool.inputSchema or {"type": "object", "properties": {}}
                tools.append({
                    "name": tool_name,
                    "description": tool.description or "",
                    "input_schema": schema,
                })
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Route a tool call to the correct MCP server and return JSON result."""
        server_name = self._tool_map.get(tool_name)
        if not server_name or server_name not in self._sessions:
            return json.dumps({"error": f"MCP tool not found: {tool_name}"})

        config = self._configs[server_name]
        raw_name = tool_name.removeprefix(f"{server_name}:") if config.tool_prefix else tool_name

        session = self._sessions[server_name]
        try:
            result = await session.call_tool(raw_name, arguments)
            if result.isError:
                return json.dumps({"error": _extract_text(result.content)})
            return _extract_text(result.content)
        except Exception as e:
            logger.warning("MCP tool '%s' failed: %s", tool_name, e)
            return json.dumps({"error": f"MCP tool {tool_name} failed: {e}"})

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tool_map

    async def _connect_one(self, config: MCPServerConfig) -> ClientSession:
        """Connect to a single MCP server using the configured transport."""
        if config.transport == "stdio":
            from mcp import StdioServerParameters

            params = StdioServerParameters(
                command=config.command,
                args=list(config.args),
                env=config.env,
            )
            transport = await self._stack.enter_async_context(stdio_client(params))
            read_stream, write_stream = transport
            session = await self._stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            return session

        if config.transport == "sse":
            transport = await self._stack.enter_async_context(sse_client(config.url))
            read_stream, write_stream = transport
            session = await self._stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            return session

        if config.transport == "streamable_http":
            transport = await self._stack.enter_async_context(
                streamablehttp_client(config.url)
            )
            read_stream, write_stream, _get_session_id = transport
            session = await self._stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            return session

        msg = f"Unsupported MCP transport: {config.transport}"
        raise ValueError(msg)

    async def _index_tools(self, config: MCPServerConfig) -> None:
        """Build tool_name -> server_name mapping for routing."""
        session = self._sessions[config.name]
        result = await session.list_tools()
        for tool in result.tools:
            prefixed = f"{config.name}:{tool.name}" if config.tool_prefix else tool.name
            self._tool_map[prefixed] = config.name


def _extract_text(content: list[Any]) -> str:
    """Extract text from MCP content blocks."""
    parts: list[str] = []
    for block in content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        else:
            parts.append(str(block))
    return "\n".join(parts) if parts else "{}"

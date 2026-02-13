from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.types import TextContent as MCPTextContent

from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.mcp_config import MCPServerConfig
from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge, _extract_text


class TestMCPServerConfig:
    def test_frozen_dataclass(self) -> None:
        config = MCPServerConfig(
            name="test",
            transport="stdio",
            command="node",
            args=("server.js",),
            tags=frozenset({"visualization"}),
        )
        assert config.name == "test"
        assert config.transport == "stdio"
        assert config.command == "node"
        assert config.args == ("server.js",)
        assert config.tags == frozenset({"visualization"})
        assert config.enabled is True
        assert config.tool_prefix is True

    def test_disabled_config(self) -> None:
        config = MCPServerConfig(name="off", transport="sse", enabled=False)
        assert config.enabled is False

    def test_sse_config_with_url(self) -> None:
        config = MCPServerConfig(
            name="remote",
            transport="sse",
            url="http://localhost:3000/sse",
        )
        assert config.url == "http://localhost:3000/sse"

    def test_no_prefix(self) -> None:
        config = MCPServerConfig(
            name="flat",
            transport="stdio",
            tool_prefix=False,
        )
        assert config.tool_prefix is False

    def test_env_dict(self) -> None:
        config = MCPServerConfig(
            name="env",
            transport="stdio",
            env={"API_KEY": "secret"},
        )
        assert config.env == {"API_KEY": "secret"}


class TestExtractText:
    def test_text_content_objects(self) -> None:
        block = MCPTextContent(type="text", text="hello")
        result = _extract_text([block])
        assert "hello" in result

    def test_dict_content(self) -> None:
        result = _extract_text([{"type": "text", "text": "world"}])
        assert result == "world"

    def test_empty_list(self) -> None:
        result = _extract_text([])
        assert result == "{}"

    def test_mixed_content(self) -> None:
        result = _extract_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}])
        assert "a" in result
        assert "b" in result


class TestMCPBridge:
    def test_initial_state(self) -> None:
        bridge = MCPBridge()
        assert bridge.connected_servers == []
        assert bridge.has_tool("anything") is False

    @pytest.mark.asyncio
    async def test_connect_skips_disabled(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(name="off", transport="stdio", enabled=False)
        await bridge.connect([config])
        assert bridge.connected_servers == []

    @pytest.mark.asyncio
    async def test_connect_handles_failure_gracefully(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(
            name="broken",
            transport="stdio",
            command="nonexistent_binary_xyz",
            args=(),
        )
        # Should not raise -- logs and continues
        await bridge.connect([config])
        assert "broken" not in bridge.connected_servers

    @pytest.mark.asyncio
    async def test_call_tool_unknown_returns_error(self) -> None:
        bridge = MCPBridge()
        result = await bridge.call_tool("nonexistent:tool", {"x": 1})
        data = json.loads(result)
        assert "error" in data
        assert "not found" in data["error"]

    @pytest.mark.asyncio
    async def test_disconnect_clears_state(self) -> None:
        bridge = MCPBridge()
        # Manually set internal state to verify cleanup
        bridge._sessions["test"] = MagicMock()  # type: ignore[assignment]
        bridge._configs["test"] = MCPServerConfig(name="test", transport="stdio")
        bridge._tool_map["test:tool"] = "test"
        await bridge.disconnect()
        assert bridge.connected_servers == []
        assert bridge.has_tool("test:tool") is False

    @pytest.mark.asyncio
    async def test_list_tools_empty_when_no_servers(self) -> None:
        bridge = MCPBridge()
        tools = await bridge.list_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_with_prefix(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(
            name="myserver",
            transport="stdio",
            tool_prefix=True,
        )
        # Mock session
        mock_session = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "do_thing"
        mock_tool.description = "Does a thing"
        mock_tool.inputSchema = {"type": "object", "properties": {"x": {"type": "string"}}}
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result

        bridge._sessions["myserver"] = mock_session
        bridge._configs["myserver"] = config

        tools = await bridge.list_tools("myserver")
        assert len(tools) == 1
        assert tools[0]["name"] == "myserver:do_thing"
        assert tools[0]["description"] == "Does a thing"

    @pytest.mark.asyncio
    async def test_list_tools_without_prefix(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(
            name="flat",
            transport="stdio",
            tool_prefix=False,
        )
        mock_session = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "do_thing"
        mock_tool.description = "Does a thing"
        mock_tool.inputSchema = {"type": "object", "properties": {}}
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result

        bridge._sessions["flat"] = mock_session
        bridge._configs["flat"] = config

        tools = await bridge.list_tools("flat")
        assert len(tools) == 1
        assert tools[0]["name"] == "do_thing"

    @pytest.mark.asyncio
    async def test_call_tool_routes_correctly(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(name="srv", transport="stdio", tool_prefix=True)

        mock_session = AsyncMock()
        mock_call_result = MagicMock()
        mock_call_result.isError = False
        mock_call_result.content = [MCPTextContent(type="text", text='{"result": "ok"}')]
        mock_session.call_tool.return_value = mock_call_result

        bridge._sessions["srv"] = mock_session
        bridge._configs["srv"] = config
        bridge._tool_map["srv:my_tool"] = "srv"

        result = await bridge.call_tool("srv:my_tool", {"arg": "val"})
        mock_session.call_tool.assert_called_once_with("my_tool", {"arg": "val"})
        assert '{"result": "ok"}' in result

    @pytest.mark.asyncio
    async def test_call_tool_error_response(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(name="srv", transport="stdio", tool_prefix=True)

        mock_session = AsyncMock()
        mock_call_result = MagicMock()
        mock_call_result.isError = True
        mock_call_result.content = [MCPTextContent(type="text", text="Something went wrong")]
        mock_session.call_tool.return_value = mock_call_result

        bridge._sessions["srv"] = mock_session
        bridge._configs["srv"] = config
        bridge._tool_map["srv:fail_tool"] = "srv"

        result = await bridge.call_tool("srv:fail_tool", {})
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(name="srv", transport="stdio", tool_prefix=True)

        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = RuntimeError("connection lost")

        bridge._sessions["srv"] = mock_session
        bridge._configs["srv"] = config
        bridge._tool_map["srv:broken_tool"] = "srv"

        result = await bridge.call_tool("srv:broken_tool", {})
        data = json.loads(result)
        assert "error" in data
        assert "connection lost" in data["error"]

    @pytest.mark.asyncio
    async def test_unsupported_transport_raises(self) -> None:
        bridge = MCPBridge()
        config = MCPServerConfig(name="bad", transport="grpc")
        with pytest.raises(ValueError, match="Unsupported MCP transport"):
            await bridge._connect_one(config)

    @pytest.mark.asyncio
    async def test_has_tool(self) -> None:
        bridge = MCPBridge()
        bridge._tool_map["srv:tool_a"] = "srv"
        assert bridge.has_tool("srv:tool_a") is True
        assert bridge.has_tool("srv:tool_b") is False


class TestToolRegistryMCPIntegration:
    @pytest.mark.asyncio
    async def test_register_mcp_tools(self) -> None:
        registry = ToolRegistry()
        bridge = MCPBridge()
        config = MCPServerConfig(
            name="ext",
            transport="stdio",
            tool_prefix=True,
            tags=frozenset({"visualization"}),
        )

        mock_session = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "draw"
        mock_tool.description = "Draw something"
        mock_tool.inputSchema = {
            "type": "object",
            "properties": {"data": {"type": "string"}},
            "required": ["data"],
        }
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result

        bridge._sessions["ext"] = mock_session
        bridge._configs["ext"] = config

        registered = await registry.register_mcp_tools(bridge, "ext", frozenset({"visualization"}))

        assert registered == ["ext:draw"]
        assert "ext:draw" in registry.list_tools()
        schema = registry.get_schema("ext:draw")
        assert schema is not None
        assert schema["description"] == "Draw something"

    @pytest.mark.asyncio
    async def test_mcp_tools_appear_in_domain_filtering(self) -> None:
        registry = ToolRegistry()
        bridge = MCPBridge()
        config = MCPServerConfig(name="viz", transport="stdio", tool_prefix=True)

        mock_session = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "render"
        mock_tool.description = "Render view"
        mock_tool.inputSchema = {"type": "object", "properties": {}}
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result

        bridge._sessions["viz"] = mock_session
        bridge._configs["viz"] = config

        await registry.register_mcp_tools(bridge, "viz", frozenset({"visualization"}))

        # Should appear when filtering for visualization domain
        domain_tools = registry.list_tools_for_domain(frozenset({"visualization"}))
        assert "viz:render" in domain_tools

        # Should NOT appear for unrelated domain
        chem_tools = registry.list_tools_for_domain(frozenset({"chemistry"}))
        assert "viz:render" not in chem_tools

    @pytest.mark.asyncio
    async def test_mcp_tool_wrapper_calls_bridge(self) -> None:
        registry = ToolRegistry()

        mock_bridge = AsyncMock(spec=MCPBridge)
        mock_bridge.list_tools.return_value = [
            {
                "name": "srv:action",
                "description": "Do action",
                "input_schema": {"type": "object", "properties": {}},
            }
        ]
        mock_bridge.call_tool.return_value = '{"done": true}'

        registered = await registry.register_mcp_tools(mock_bridge, "srv", frozenset())
        assert registered == ["srv:action"]

        func = registry.get("srv:action")
        assert func is not None
        result = await func(x="test")
        mock_bridge.call_tool.assert_called_once_with("srv:action", {"x": "test"})
        assert result == '{"done": true}'

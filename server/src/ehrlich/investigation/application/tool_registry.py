from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, get_type_hints

if TYPE_CHECKING:
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge

ToolFunction = Callable[..., Any]

_PYTHON_TO_JSON_SCHEMA: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFunction] = {}
        self._schemas: dict[str, dict[str, Any]] = {}
        self._tags: dict[str, frozenset[str]] = {}

    def register(
        self,
        name: str,
        func: ToolFunction,
        tags: frozenset[str] | None = None,
    ) -> None:
        self._tools[name] = func
        self._schemas[name] = _generate_schema(name, func)
        self._tags[name] = tags or frozenset()

    def get(self, name: str) -> ToolFunction | None:
        return self._tools.get(name)

    def get_schema(self, name: str) -> dict[str, Any] | None:
        return self._schemas.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def list_schemas(self) -> list[dict[str, Any]]:
        return list(self._schemas.values())

    def list_tools_for_domain(self, domain_tags: frozenset[str]) -> list[str]:
        """Return tool names matching any of the domain tags, plus untagged tools."""
        return [
            name
            for name, tags in self._tags.items()
            if not tags or tags & domain_tags
        ]

    def list_schemas_for_domain(
        self, domain_tags: frozenset[str]
    ) -> list[dict[str, Any]]:
        """Return tool schemas matching any of the domain tags, plus untagged tools."""
        allowed = set(self.list_tools_for_domain(domain_tags))
        return [s for s in self._schemas.values() if s["name"] in allowed]

    async def register_mcp_tools(
        self,
        bridge: MCPBridge,
        server_name: str,
        tags: frozenset[str] | None = None,
    ) -> list[str]:
        """Register all tools from an MCP server via the bridge.

        Returns the list of registered tool names.
        """
        tool_schemas = await bridge.list_tools(server_name)
        registered: list[str] = []
        for schema in tool_schemas:
            name = schema["name"]
            self._schemas[name] = schema

            async def _mcp_wrapper(
                _bridge: MCPBridge = bridge,
                _name: str = name,
                **kwargs: Any,
            ) -> str:
                return await _bridge.call_tool(_name, kwargs)

            self._tools[name] = _mcp_wrapper
            self._tags[name] = tags or frozenset()
            registered.append(name)
        return registered


def _generate_schema(name: str, func: ToolFunction) -> dict[str, Any]:
    sig = inspect.signature(func)
    docstring = inspect.getdoc(func) or ""
    hints = get_type_hints(func)
    param_docs = _parse_param_docs(docstring)
    description = _extract_description(docstring)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        param_type = hints.get(param_name, str)
        json_type = _python_type_to_json(param_type)
        prop: dict[str, Any] = {"type": json_type}

        if param_name in param_docs:
            prop["description"] = param_docs[param_name]

        if json_type == "array":
            item_type = _get_list_item_type(param_type)
            prop["items"] = {"type": item_type}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        elif param.default is not None:
            prop["default"] = param.default

        properties[param_name] = prop

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        input_schema["required"] = required

    return {
        "name": name,
        "description": description,
        "input_schema": input_schema,
    }


def _extract_description(docstring: str) -> str:
    lines = docstring.strip().split("\n")
    desc_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith(("args:", "params:", "parameters:", "returns:", "raises:")):
            break
        desc_lines.append(stripped)
    return " ".join(desc_lines).strip() or "No description."


def _parse_param_docs(docstring: str) -> dict[str, str]:
    params: dict[str, str] = {}
    pattern = re.compile(r"^\s*(\w+)\s*[:\-]\s*(.+)$")
    in_params = False
    for line in docstring.split("\n"):
        stripped = line.strip().lower()
        if stripped in ("args:", "params:", "parameters:"):
            in_params = True
            continue
        if stripped in ("returns:", "raises:", ""):
            if in_params and stripped:
                break
            continue
        if in_params:
            match = pattern.match(line.strip())
            if match:
                params[match.group(1)] = match.group(2).strip()
    return params


def _python_type_to_json(python_type: type) -> str:
    if python_type in _PYTHON_TO_JSON_SCHEMA:
        return _PYTHON_TO_JSON_SCHEMA[python_type]

    origin = getattr(python_type, "__origin__", None)
    if origin is list:
        return "array"

    return "string"


def _get_list_item_type(python_type: type) -> str:
    args = getattr(python_type, "__args__", None)
    if args and len(args) > 0:
        return _PYTHON_TO_JSON_SCHEMA.get(args[0], "string")
    return "string"

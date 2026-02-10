from ehrlich.investigation.application.tool_registry import ToolRegistry


async def sample_tool(query: str, limit: int = 10) -> str:
    """Search for papers by query string."""
    return f"Found {limit} results for {query}"


async def tool_with_list(smiles_list: list[str], model_id: str) -> str:
    """Predict activity for a list of SMILES."""
    return "predictions"


async def tool_no_docstring(x: str) -> str:
    return x


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        registry.register("sample", sample_tool)
        assert registry.get("sample") is sample_tool

    def test_get_unknown_returns_none(self) -> None:
        registry = ToolRegistry()
        assert registry.get("unknown") is None

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register("tool_a", sample_tool)
        registry.register("tool_b", tool_with_list)
        assert set(registry.list_tools()) == {"tool_a", "tool_b"}

    def test_list_schemas(self) -> None:
        registry = ToolRegistry()
        registry.register("sample", sample_tool)
        schemas = registry.list_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "sample"


class TestSchemaGeneration:
    def test_basic_schema(self) -> None:
        registry = ToolRegistry()
        registry.register("sample", sample_tool)
        schema = registry.get_schema("sample")
        assert schema is not None
        assert schema["name"] == "sample"
        assert "Search for papers" in schema["description"]
        props = schema["input_schema"]["properties"]
        assert "query" in props
        assert props["query"]["type"] == "string"
        assert "limit" in props
        assert props["limit"]["type"] == "integer"
        assert schema["input_schema"]["required"] == ["query"]

    def test_list_param_schema(self) -> None:
        registry = ToolRegistry()
        registry.register("predict", tool_with_list)
        schema = registry.get_schema("predict")
        assert schema is not None
        props = schema["input_schema"]["properties"]
        assert props["smiles_list"]["type"] == "array"
        assert props["smiles_list"]["items"]["type"] == "string"
        assert set(schema["input_schema"]["required"]) == {"smiles_list", "model_id"}

    def test_no_docstring(self) -> None:
        registry = ToolRegistry()
        registry.register("nodoc", tool_no_docstring)
        schema = registry.get_schema("nodoc")
        assert schema is not None
        assert schema["description"] == "No description."

    def test_default_value_in_schema(self) -> None:
        registry = ToolRegistry()
        registry.register("sample", sample_tool)
        schema = registry.get_schema("sample")
        assert schema is not None
        props = schema["input_schema"]["properties"]
        assert props["limit"]["default"] == 10

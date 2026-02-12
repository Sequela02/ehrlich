# MCP Server Development

## What is MCP

Open protocol by Anthropic standardizing how LLM apps connect to external tools and data. Client-host-server architecture (like LSP).

Three primitives:
- **Tools** (model-controlled): functions the LLM can discover and invoke
- **Resources** (app-controlled): read-only data identified by URIs
- **Prompts** (user-controlled): reusable message templates

Communication: JSON-RPC 2.0 over stdio (subprocess) or Streamable HTTP.

## Building a Python MCP Server

SDK: `pip install "mcp[cli]"` (pin to `mcp>=1.25,<2`)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ehrlich-server")

@mcp.tool()
def run_experiment(hypothesis: str, parameters: dict) -> str:
    """Execute a scientific experiment with given parameters."""
    # ... execute ML pipeline
    return json.dumps(result)

if __name__ == "__main__":
    mcp.run()  # defaults to stdio
```

Key points:
- Docstrings become tool descriptions that Claude sees
- Type hints auto-generate JSON Schema for parameters
- Use `Annotated[str, Field(description="...")]` from Pydantic for richer descriptions
- Supports both sync and async functions
- Keep under 20 tools per server

## How Claude Calls Tools

Loop: think -> act -> observe -> repeat
1. User sends message
2. Claude receives message + tool definitions (from `tools/list`)
3. Claude decides which tool(s) to call
4. Client executes `tools/call` against MCP server
5. Result injected back into conversation
6. Claude decides: call another tool, or respond
7. Loop until `stop_reason: "end_turn"`

## Code Execution MCP Servers (Reference)

- **pydantic/mcp-run-python** — sandboxed Python via Pyodide/WASM in Deno. Limitation: only pure-Python packages + pre-compiled WASM packages.
- **yzfly/mcp-python-interpreter** — runs Python in local environments. Less sandboxed, more capable.
- **elusznik/mcp-server-code-execution-mode** — Docker/Podman containers.

For our use case: we build our own MCP server with domain-specific tools, not a generic code executor.

## Gotchas

- **stdio: never print to stdout** — corrupts JSON-RPC messages. Use stderr for logging.
- **v1 vs v2 SDK** — pin to v1, v2 is pre-alpha
- **FastMCP import** — use `from mcp.server.fastmcp import FastMCP` (official SDK), not the standalone `fastmcp` package
- **Error handling** — return errors as content with `is_error=True`, don't throw exceptions
- **Tool count** — keep under 20 per server (Claude Code uses ~12)
- **Testing** — `npx @modelcontextprotocol/inspector` for interactive testing

## Sources

- MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Build an MCP Server: https://modelcontextprotocol.io/docs/develop/build-server
- Code Execution with MCP: https://www.anthropic.com/engineering/code-execution-with-mcp

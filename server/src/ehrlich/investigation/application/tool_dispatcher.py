from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.tool_cache import ToolCache

if TYPE_CHECKING:
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.investigation import Investigation
    from ehrlich.investigation.domain.repository import InvestigationRepository
    from ehrlich.investigation.domain.uploaded_file import UploadedFile

logger = logging.getLogger(__name__)


class ToolDispatcher:
    def __init__(
        self,
        registry: ToolRegistry,
        cache: ToolCache,
        repository: InvestigationRepository | None,
        uploaded_files: dict[str, UploadedFile],
    ) -> None:
        self._registry = registry
        self._cache = cache
        self._repository = repository
        self._uploaded_files = uploaded_files

    def update_uploaded_files(self, files: dict[str, UploadedFile]) -> None:
        self._uploaded_files = files

    async def dispatch(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        investigation: Investigation,
    ) -> str:
        # Intercept query_uploaded_data -- serve from in-memory file store
        if tool_name == "query_uploaded_data":
            return self._handle_query_uploaded_data(tool_input)

        # Intercept search_prior_research -- query FTS5 via repository
        if tool_name == "search_prior_research" and self._repository:
            query = tool_input.get("query", "")
            limit = int(tool_input.get("limit", 10))
            results = await self._repository.search_findings(query, limit)
            return json.dumps({"results": results, "count": len(results), "query": query})

        args_hash = ToolCache.hash_args(tool_input)
        cached = self._cache.get(tool_name, args_hash)
        if cached is not None:
            return cached

        func = self._registry.get(tool_name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await func(**tool_input)
            result_str = str(result)
            self._cache.put(tool_name, args_hash, result_str)
            return result_str
        except Exception:
            logger.exception("Tool %s failed", tool_name)
            return json.dumps({"error": f"Tool {tool_name} failed"})

    def _handle_query_uploaded_data(self, tool_input: dict[str, Any]) -> str:
        """Handle query_uploaded_data tool calls from in-memory uploaded files."""
        import pandas as pd

        file_id = tool_input.get("file_id", "")
        uploaded = self._uploaded_files.get(file_id)
        if uploaded is None:
            return json.dumps({"error": f"File not found: {file_id}"})

        # Document files: return text content
        if uploaded.document:
            keyword = tool_input.get("filter_value", "")
            text = uploaded.document.text
            if keyword:
                lines = [ln for ln in text.split("\n") if keyword.lower() in ln.lower()]
                text = "\n".join(lines) if lines else f"No lines matching '{keyword}'"
            return json.dumps(
                {
                    "file_id": file_id,
                    "filename": uploaded.filename,
                    "type": "document",
                    "page_count": uploaded.document.page_count,
                    "text": text,
                }
            )

        # Tabular files: reconstruct DataFrame from sample data and query
        if uploaded.tabular is None:
            return json.dumps({"error": "File has no queryable data"})

        tab = uploaded.tabular
        rows = [list(row) for row in tab.sample_rows]
        df = pd.DataFrame(rows, columns=list(tab.columns))

        # Apply type coercion for numeric columns
        for col, dtype_str in zip(tab.columns, tab.dtypes, strict=True):
            if "int" in dtype_str or "float" in dtype_str:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Column selection
        columns_str = tool_input.get("columns")
        if columns_str:
            selected = [c.strip() for c in columns_str.split(",")]
            valid = [c for c in selected if c in df.columns]
            if valid:
                df = df[valid]

        # Filtering
        filter_col = tool_input.get("filter_column")
        filter_op = tool_input.get("filter_op")
        filter_val = tool_input.get("filter_value")
        if filter_col and filter_op and filter_val is not None and filter_col in df.columns:
            col_series = df[filter_col]
            ops: dict[str, Any] = {
                "eq": lambda s, v: s == v,
                "gt": lambda s, v: s > v,
                "lt": lambda s, v: s < v,
                "gte": lambda s, v: s >= v,
                "lte": lambda s, v: s <= v,
                "contains": lambda s, v: s.astype(str).str.contains(str(v), case=False, na=False),
            }
            op_func = ops.get(filter_op)
            if op_func:
                import contextlib

                cast_val: Any = filter_val
                if filter_op != "contains":
                    with contextlib.suppress(ValueError, TypeError):
                        cast_val = float(filter_val)
                with contextlib.suppress(TypeError, ValueError):
                    mask = op_func(col_series, cast_val)
                    df = df[mask]

        head_n = min(int(tool_input.get("head", 50)), 200)
        df = df.head(head_n)

        return json.dumps(
            {
                "file_id": file_id,
                "filename": uploaded.filename,
                "type": "tabular",
                "total_rows": tab.row_count,
                "returned_rows": len(df),
                "columns": list(df.columns),
                "data": df.values.tolist(),
            }
        )

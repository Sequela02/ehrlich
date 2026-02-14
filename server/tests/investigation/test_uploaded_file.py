from __future__ import annotations

import json

import pytest

from ehrlich.investigation.domain.uploaded_file import (
    DocumentData,
    TabularData,
    UploadedFile,
)


class TestUploadedFile:
    def test_tabular_file(self) -> None:
        tab = TabularData(
            columns=("a", "b"),
            dtypes=("int64", "float64"),
            row_count=2,
            summary_stats={"a": {"mean": 1.5}},
            sample_rows=(("1", "2.0"), ("2", "3.0")),
        )
        f = UploadedFile(filename="data.csv", content_type="text/csv", tabular=tab)
        assert f.filename == "data.csv"
        assert f.tabular is not None
        assert f.document is None
        assert len(f.file_id) == 36

    def test_document_file(self) -> None:
        doc = DocumentData(text="Hello world", page_count=1)
        f = UploadedFile(filename="report.pdf", content_type="application/pdf", document=doc)
        assert f.document is not None
        assert f.tabular is None
        assert f.document.page_count == 1

    def test_must_have_data(self) -> None:
        with pytest.raises(ValueError, match="either tabular or document"):
            UploadedFile(filename="empty.csv", content_type="text/csv")

    def test_filename_required(self) -> None:
        tab = TabularData(
            columns=("x",),
            dtypes=("int64",),
            row_count=1,
            summary_stats={},
            sample_rows=(("1",),),
        )
        with pytest.raises(ValueError, match="filename"):
            UploadedFile(filename="", content_type="text/csv", tabular=tab)

    def test_frozen(self) -> None:
        tab = TabularData(
            columns=("x",),
            dtypes=("int64",),
            row_count=1,
            summary_stats={},
            sample_rows=(("1",),),
        )
        f = UploadedFile(filename="f.csv", content_type="text/csv", tabular=tab)
        with pytest.raises(AttributeError):
            f.filename = "other.csv"  # type: ignore[misc]


class TestQueryUploadedDataHandler:
    """Test the orchestrator's _handle_query_uploaded_data method."""

    def _make_orchestrator(self) -> object:
        """Create a minimal orchestrator with uploaded files."""
        from unittest.mock import MagicMock

        from ehrlich.investigation.application.multi_orchestrator import (
            MultiModelOrchestrator,
        )

        orch = MultiModelOrchestrator(
            director=MagicMock(),
            researcher=MagicMock(),
            summarizer=MagicMock(),
            registry=MagicMock(),
        )

        tab = TabularData(
            columns=("name", "age", "score"),
            dtypes=("object", "int64", "float64"),
            row_count=3,
            summary_stats={"age": {"mean": 30.0}, "score": {"mean": 85.0}},
            sample_rows=(
                ("Alice", "30", "85.5"),
                ("Bob", "25", "92.0"),
                ("Charlie", "35", "78.3"),
            ),
        )
        tabular_file = UploadedFile(
            file_id="tab-123",
            filename="data.csv",
            content_type="text/csv",
            tabular=tab,
        )

        doc = DocumentData(text="This is a test document about education policy.", page_count=2)
        doc_file = UploadedFile(
            file_id="doc-456",
            filename="report.pdf",
            content_type="application/pdf",
            document=doc,
        )

        orch._uploaded_files = {"tab-123": tabular_file, "doc-456": doc_file}
        orch._dispatcher.update_uploaded_files(orch._uploaded_files)
        return orch

    def test_query_all_columns(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(orch._dispatcher._handle_query_uploaded_data({"file_id": "tab-123"}))
        assert result["type"] == "tabular"
        assert result["returned_rows"] == 3
        assert result["columns"] == ["name", "age", "score"]

    def test_query_specific_columns(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "tab-123",
                    "columns": "name,score",
                }
            )
        )
        assert result["columns"] == ["name", "score"]

    def test_query_filter_eq(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "tab-123",
                    "filter_column": "name",
                    "filter_op": "eq",
                    "filter_value": "Alice",
                }
            )
        )
        assert result["returned_rows"] == 1

    def test_query_filter_gt(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "tab-123",
                    "filter_column": "age",
                    "filter_op": "gt",
                    "filter_value": "28",
                }
            )
        )
        assert result["returned_rows"] == 2  # Alice (30) and Charlie (35)

    def test_query_head_limit(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "tab-123",
                    "head": 2,
                }
            )
        )
        assert result["returned_rows"] == 2

    def test_query_not_found(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(orch._dispatcher._handle_query_uploaded_data({"file_id": "missing"}))
        assert "error" in result

    def test_query_document(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(orch._dispatcher._handle_query_uploaded_data({"file_id": "doc-456"}))
        assert result["type"] == "document"
        assert "education policy" in result["text"]
        assert result["page_count"] == 2

    def test_query_document_keyword_filter(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "doc-456",
                    "filter_value": "education",
                }
            )
        )
        assert "education" in result["text"].lower()

    def test_query_filter_contains(self) -> None:
        orch = self._make_orchestrator()
        result = json.loads(
            orch._dispatcher._handle_query_uploaded_data(
                {
                    "file_id": "tab-123",
                    "filter_column": "name",
                    "filter_op": "contains",
                    "filter_value": "li",
                }
            )
        )
        # Alice and Charlie contain "li"
        assert result["returned_rows"] == 2


class TestPromptInjection:
    def test_empty_files(self) -> None:
        from ehrlich.investigation.application.prompts.builders import (
            build_uploaded_data_context,
        )

        assert build_uploaded_data_context([]) == ""

    def test_tabular_context(self) -> None:
        from ehrlich.investigation.application.prompts.builders import (
            build_uploaded_data_context,
        )

        tab = TabularData(
            columns=("x", "y"),
            dtypes=("int64", "float64"),
            row_count=10,
            summary_stats={"x": {"mean": 5.0, "std": 2.0}},
            sample_rows=(("1", "2.0"), ("3", "4.0")),
        )
        f = UploadedFile(filename="data.csv", content_type="text/csv", tabular=tab)
        ctx = build_uploaded_data_context([f])
        assert "<uploaded_data>" in ctx
        assert "data.csv" in ctx
        assert "x, y" in ctx or "x" in ctx
        assert "10" in ctx
        assert "</uploaded_data>" in ctx

    def test_document_context(self) -> None:
        from ehrlich.investigation.application.prompts.builders import (
            build_uploaded_data_context,
        )

        doc = DocumentData(text="Test content here", page_count=3)
        f = UploadedFile(filename="report.pdf", content_type="application/pdf", document=doc)
        ctx = build_uploaded_data_context([f])
        assert "<uploaded_data>" in ctx
        assert "report.pdf" in ctx
        assert "Test content" in ctx
        assert "3" in ctx

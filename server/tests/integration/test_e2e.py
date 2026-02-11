"""End-to-end smoke test for the investigation pipeline.

Mocks the Anthropic API but exercises the full pipeline:
tool registry build, orchestrator dispatch, SSE event generation.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ehrlich.api.routes.investigation import _build_registry
from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.investigation.application.orchestrator import Orchestrator
from ehrlich.investigation.domain.events import ToolResultEvent
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.infrastructure.anthropic_client import MessageResponse


def _make_response(
    content: list[dict[str, Any]],
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> MessageResponse:
    return MessageResponse(
        content=content,
        stop_reason=stop_reason,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _text(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _tool(tool_id: str, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


class TestToolRegistry:
    def test_build_registry_has_expected_tools(self) -> None:
        registry = _build_registry()
        tools = registry.list_tools()
        assert len(tools) == 23
        assert "validate_smiles" in tools
        assert "search_literature" in tools
        assert "explore_dataset" in tools
        assert "train_model" in tools
        assert "dock_against_target" in tools
        assert "record_finding" in tools
        assert "conclude_investigation" in tools
        assert "propose_hypothesis" in tools
        assert "design_experiment" in tools
        assert "evaluate_hypothesis" in tools
        assert "record_negative_control" in tools

    def test_all_tools_have_schemas(self) -> None:
        registry = _build_registry()
        schemas = registry.list_schemas()
        assert len(schemas) == 23
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "input_schema" in schema


class TestE2EPipeline:
    @pytest.mark.asyncio
    async def test_full_investigation_flow(self) -> None:
        """Simulate a full investigation: literature -> chemistry -> finding -> conclude."""
        registry = _build_registry()
        mock_client = AsyncMock()
        mock_client.model = "claude-opus-4-6"

        mock_client.create_message.side_effect = [
            # Turn 1: Claude searches literature
            _make_response(
                content=[
                    _text("I'll begin by reviewing literature on MRSA."),
                    _tool("tu_1", "search_literature", {"query": "MRSA antimicrobial resistance"}),
                ],
                stop_reason="tool_use",
            ),
            # Turn 2: Claude validates a SMILES
            _make_response(
                content=[
                    _text("Let me validate a candidate molecule."),
                    _tool("tu_2", "validate_smiles", {"smiles": "CC(=O)Oc1ccccc1C(=O)O"}),
                ],
                stop_reason="tool_use",
            ),
            # Turn 3: Claude records a finding and concludes
            _make_response(
                content=[
                    _tool(
                        "tu_3",
                        "record_finding",
                        {
                            "title": "Aspirin shows activity",
                            "detail": "Aspirin has antimicrobial properties",
                            "hypothesis_id": "h1",
                            "evidence_type": "supporting",
                        },
                    ),
                    _tool(
                        "tu_4",
                        "conclude_investigation",
                        {
                            "summary": "Found potential MRSA candidates",
                            "candidates": [
                                {
                                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                                    "name": "Aspirin analog",
                                    "rationale": "Repurposed antimicrobial",
                                },
                            ],
                            "citations": ["Smith 2024"],
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
        ]

        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=10)
        investigation = Investigation(prompt="Find antimicrobials for MRSA")

        events = []
        async for event in orchestrator.run(investigation):
            events.append(event)

        # Verify event types
        event_types = [type(e).__name__ for e in events]
        assert "Thinking" in event_types
        assert "ToolCalled" in event_types
        assert "ToolResultEvent" in event_types
        assert "FindingRecorded" in event_types
        assert "InvestigationCompleted" in event_types

        # Verify investigation state
        assert investigation.status == InvestigationStatus.COMPLETED
        assert len(investigation.findings) == 1
        assert investigation.findings[0].title == "Aspirin shows activity"
        assert len(investigation.candidates) == 1
        assert investigation.candidates[0].smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert investigation.summary == "Found potential MRSA candidates"
        assert len(investigation.citations) == 1

        # Verify tool results have preview text
        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        for tr in tool_results:
            assert len(tr.result_preview) > 0

    @pytest.mark.asyncio
    async def test_sse_event_generation(self) -> None:
        """Verify all domain events convert to SSE events."""
        registry = _build_registry()
        mock_client = AsyncMock()
        mock_client.model = "claude-opus-4-6"

        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _text("Starting investigation."),
                    _tool("tu_1", "search_literature", {"query": "MRSA"}),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text("Done.")],
                stop_reason="end_turn",
            ),
        ]

        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        sse_events = []
        async for domain_event in orchestrator.run(investigation):
            sse = domain_event_to_sse(domain_event)
            assert sse is not None, f"No SSE mapping for {type(domain_event).__name__}"
            sse_events.append(sse)

        event_types = {e.event for e in sse_events}
        assert SSEEventType.THINKING in event_types
        assert SSEEventType.TOOL_CALLED in event_types
        assert SSEEventType.TOOL_RESULT in event_types
        assert SSEEventType.COMPLETED in event_types

        # Verify format() produces valid JSON
        for sse in sse_events:
            parsed = json.loads(sse.format())
            assert "event" in parsed
            assert "data" in parsed

    @pytest.mark.asyncio
    async def test_chemistry_tool_dispatch(self) -> None:
        """Verify chemistry tools dispatch correctly through orchestrator."""
        registry = _build_registry()
        mock_client = AsyncMock()
        mock_client.model = "claude-opus-4-6"

        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool("tu_1", "compute_descriptors", {"smiles": "CCO"}),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text("Done.")],
                stop_reason="end_turn",
            ),
        ]

        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Analyze ethanol")

        events = []
        async for event in orchestrator.run(investigation):
            events.append(event)

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) == 1
        result = json.loads(tool_results[0].result_preview)
        assert "molecular_weight" in result or "smiles" in result

    @pytest.mark.asyncio
    async def test_prediction_tool_dispatch(self) -> None:
        """Verify prediction tools return proper error for missing model."""
        registry = _build_registry()
        mock_client = AsyncMock()
        mock_client.model = "claude-opus-4-6"

        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool(
                        "tu_1",
                        "predict_candidates",
                        {"smiles_list": ["CCO"], "model_id": "nonexistent"},
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text("Done.")],
                stop_reason="end_turn",
            ),
        ]

        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Predict")

        events = []
        async for event in orchestrator.run(investigation):
            events.append(event)

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) == 1
        result = json.loads(tool_results[0].result_preview)
        assert "error" in result

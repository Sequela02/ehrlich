"""End-to-end smoke test for the investigation pipeline.

Mocks the Anthropic API but exercises the full pipeline:
tool registry build, orchestrator dispatch, SSE event generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ehrlich.api.routes.investigation import _build_registry
from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.domain.events import ToolResultEvent
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus


@dataclass(frozen=True)
class FakeResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int


def _make_response(
    content: list[dict[str, Any]],
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> FakeResponse:
    return FakeResponse(
        content=content,
        stop_reason=stop_reason,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _text(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _tool(tool_id: str, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


def _formulation_json() -> str:
    return json.dumps(
        {
            "hypotheses": [
                {
                    "statement": "Aspirin analogs show antimicrobial activity against MRSA",
                    "rationale": "Literature suggests repurposing potential",
                },
            ],
            "negative_controls": [],
        }
    )


def _experiment_design_json() -> str:
    return json.dumps(
        {
            "description": "Validate and analyze aspirin analogs",
            "tool_plan": ["validate_smiles", "compute_descriptors"],
            "success_criteria": "Valid SMILES with drug-like properties",
            "failure_criteria": "Invalid or non-drug-like",
        }
    )


def _evaluation_json() -> str:
    return json.dumps(
        {
            "status": "supported",
            "confidence": 0.75,
            "reasoning": "Aspirin analogs show promising properties",
        }
    )


def _synthesis_json() -> str:
    return json.dumps(
        {
            "summary": "Found potential MRSA candidates via aspirin analog repurposing.",
            "candidates": [
                {
                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                    "name": "Aspirin analog",
                    "rationale": "Repurposed antimicrobial",
                    "rank": 1,
                },
            ],
            "citations": ["Smith 2024"],
        }
    )


def _make_clients() -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    director = AsyncMock()
    director.model = "claude-opus-4-6"
    researcher = AsyncMock()
    researcher.model = "claude-sonnet-4-5-20250929"
    summarizer = AsyncMock()
    summarizer.model = "claude-haiku-4-5-20251001"
    return director, researcher, summarizer


class TestToolRegistry:
    def test_build_registry_has_expected_tools(self) -> None:
        registry = _build_registry()
        tools = registry.list_tools()
        assert len(tools) == 42
        assert "validate_smiles" in tools
        assert "search_literature" in tools
        assert "search_citations" in tools
        assert "explore_dataset" in tools
        assert "train_model" in tools
        assert "dock_against_target" in tools
        assert "record_finding" in tools
        assert "conclude_investigation" in tools
        assert "propose_hypothesis" in tools
        assert "design_experiment" in tools
        assert "evaluate_hypothesis" in tools
        assert "record_negative_control" in tools
        assert "get_protein_annotation" in tools
        assert "search_disease_targets" in tools
        assert "search_pharmacology" in tools
        assert "search_prior_research" in tools
        # Sports science tools
        assert "search_sports_literature" in tools
        assert "analyze_training_evidence" in tools
        assert "compare_protocols" in tools
        assert "assess_injury_risk" in tools
        assert "compute_training_metrics" in tools
        assert "search_supplement_evidence" in tools
        # Sports science tools (new)
        assert "search_clinical_trials" in tools
        assert "search_supplement_labels" in tools
        assert "search_nutrient_data" in tools
        assert "search_supplement_safety" in tools

    def test_all_tools_have_schemas(self) -> None:
        registry = _build_registry()
        schemas = registry.list_schemas()
        assert len(schemas) == 42
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "input_schema" in schema


class TestE2EPipeline:
    @pytest.mark.asyncio
    async def test_full_investigation_flow(self) -> None:
        """Simulate a full investigation with multi-model orchestrator."""
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_response([_text(_formulation_json())]),
                _make_response([_text(_experiment_design_json())]),
                _make_response([_text(_evaluation_json())]),
                _make_response([_text(_synthesis_json())]),
            ]
        )
        researcher.create_message = AsyncMock(
            side_effect=[
                # Literature survey: end_turn
                _make_response([_text("Literature done.")]),
                # Experiment: validate_smiles then end_turn
                _make_response(
                    [
                        _text("Let me validate."),
                        _tool("tu_1", "validate_smiles", {"smiles": "CC(=O)Oc1ccccc1C(=O)O"}),
                    ],
                    stop_reason="tool_use",
                ),
                _make_response([_text("Experiment done.")]),
            ]
        )

        registry = _build_registry()
        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_experiment=5,
        )
        investigation = Investigation(prompt="Find antimicrobials for MRSA")

        events = []
        async for event in orchestrator.run(investigation):
            events.append(event)

        event_types = [type(e).__name__ for e in events]
        assert "Thinking" in event_types
        assert "ToolCalled" in event_types
        assert "ToolResultEvent" in event_types
        assert "InvestigationCompleted" in event_types
        assert investigation.status == InvestigationStatus.COMPLETED
        assert len(investigation.candidates) == 1

    @pytest.mark.asyncio
    async def test_sse_event_generation(self) -> None:
        """Verify all domain events convert to SSE events."""
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_response([_text(_formulation_json())]),
                _make_response([_text(_experiment_design_json())]),
                _make_response([_text(_evaluation_json())]),
                _make_response([_text(_synthesis_json())]),
            ]
        )
        researcher.create_message = AsyncMock(
            return_value=_make_response([_text("Done.")])
        )

        registry = _build_registry()
        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_experiment=1,
        )
        investigation = Investigation(prompt="Test")

        sse_events = []
        async for domain_event in orchestrator.run(investigation):
            sse = domain_event_to_sse(domain_event)
            if sse is not None:
                sse_events.append(sse)

        event_types = {e.event for e in sse_events}
        assert SSEEventType.THINKING in event_types
        assert SSEEventType.COMPLETED in event_types

        for sse in sse_events:
            parsed = json.loads(sse.format())
            assert "event" in parsed
            assert "data" in parsed

    @pytest.mark.asyncio
    async def test_chemistry_tool_dispatch(self) -> None:
        """Verify chemistry tools dispatch correctly through orchestrator."""
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_response([_text(_formulation_json())]),
                _make_response([_text(_experiment_design_json())]),
                _make_response([_text(_evaluation_json())]),
                _make_response([_text(_synthesis_json())]),
            ]
        )
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_response([_text("Lit done.")]),
                _make_response(
                    [_tool("tu_1", "compute_descriptors", {"smiles": "CCO"})],
                    stop_reason="tool_use",
                ),
                _make_response([_text("Experiment done.")]),
            ]
        )

        registry = _build_registry()
        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_experiment=5,
        )
        investigation = Investigation(prompt="Analyze ethanol")

        events = []
        async for event in orchestrator.run(investigation):
            events.append(event)

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) >= 1

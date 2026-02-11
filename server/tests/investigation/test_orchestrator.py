from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ehrlich.investigation.application.orchestrator import Orchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.events import (
    ExperimentStarted,
    FindingRecorded,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    NegativeControlRecorded,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)
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


def _text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _tool_use_block(tool_id: str, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock()
    client.model = "claude-opus-4-6"
    return client


@pytest.fixture
def registry() -> ToolRegistry:
    registry = ToolRegistry()

    async def mock_search_literature(query: str, limit: int = 10) -> str:
        """Search scientific literature for papers."""
        return json.dumps({"query": query, "count": 1, "papers": []})

    async def mock_validate_smiles(smiles: str) -> str:
        """Validate a SMILES string."""
        return json.dumps({"smiles": smiles, "valid": True})

    from ehrlich.investigation.tools import (
        conclude_investigation,
        design_experiment,
        evaluate_hypothesis,
        propose_hypothesis,
        record_finding,
        record_negative_control,
    )

    registry.register("search_literature", mock_search_literature)
    registry.register("validate_smiles", mock_validate_smiles)
    registry.register("record_finding", record_finding)
    registry.register("conclude_investigation", conclude_investigation)
    registry.register("propose_hypothesis", propose_hypothesis)
    registry.register("design_experiment", design_experiment)
    registry.register("evaluate_hypothesis", evaluate_hypothesis)
    registry.register("record_negative_control", record_negative_control)
    return registry


async def _collect_events(orchestrator: Orchestrator, investigation: Investigation) -> list[Any]:
    events = []
    async for event in orchestrator.run(investigation):
        events.append(event)
    return events


class TestOrchestratorTextOnly:
    @pytest.mark.asyncio
    async def test_single_text_response(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.return_value = _make_response(
            content=[_text_block("I'll begin the investigation.")],
            stop_reason="end_turn",
        )
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Find antimicrobials for MRSA")

        events = await _collect_events(orchestrator, investigation)

        thinking_events = [e for e in events if isinstance(e, Thinking)]
        completed_events = [e for e in events if isinstance(e, InvestigationCompleted)]
        assert len(thinking_events) == 1
        assert thinking_events[0].text == "I'll begin the investigation."
        assert len(completed_events) == 1
        assert investigation.status == InvestigationStatus.COMPLETED


class TestOrchestratorToolDispatch:
    @pytest.mark.asyncio
    async def test_tool_call_and_result(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _text_block("Let me search the literature."),
                    _tool_use_block("tu_1", "search_literature", {"query": "MRSA"}),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Investigation complete.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Find antimicrobials for MRSA")

        events = await _collect_events(orchestrator, investigation)

        tool_called = [e for e in events if isinstance(e, ToolCalled)]
        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_called) == 1
        assert tool_called[0].tool_name == "search_literature"
        assert len(tool_results) == 1

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[_tool_use_block("tu_1", "nonexistent_tool", {})],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) == 1
        assert "error" in tool_results[0].result_preview.lower()


class TestOrchestratorControlTools:
    @pytest.mark.asyncio
    async def test_propose_hypothesis_creates_entity(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "propose_hypothesis",
                        {
                            "statement": "Thiazolidine compounds are active against MRSA",
                            "rationale": "Literature suggests activity",
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        assert len(investigation.hypotheses) == 1
        statement = investigation.hypotheses[0].statement
        assert statement == "Thiazolidine compounds are active against MRSA"
        hyp_events = [e for e in events if isinstance(e, HypothesisFormulated)]
        assert len(hyp_events) == 1

    @pytest.mark.asyncio
    async def test_design_experiment_creates_entity(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "propose_hypothesis",
                        {"statement": "Test hypothesis", "rationale": "Reason"},
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_2",
                        "design_experiment",
                        {
                            "hypothesis_id": "",  # will be filled from investigation state
                            "description": "Test binding",
                            "tool_plan": ["dock_against_target"],
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        assert len(investigation.experiments) == 1
        exp_events = [e for e in events if isinstance(e, ExperimentStarted)]
        assert len(exp_events) == 1

    @pytest.mark.asyncio
    async def test_record_finding_links_to_hypothesis(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "record_finding",
                        {
                            "title": "Key insight",
                            "detail": "Important detail",
                            "hypothesis_id": "h1",
                            "evidence_type": "supporting",
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        assert len(investigation.findings) == 1
        assert investigation.findings[0].hypothesis_id == "h1"
        assert investigation.findings[0].evidence_type == "supporting"
        finding_events = [e for e in events if isinstance(e, FindingRecorded)]
        assert len(finding_events) == 1
        assert finding_events[0].evidence_type == "supporting"

    @pytest.mark.asyncio
    async def test_evaluate_hypothesis_updates_status(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "propose_hypothesis",
                        {"statement": "Test", "rationale": "Reason"},
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_2",
                        "evaluate_hypothesis",
                        {
                            "hypothesis_id": "",  # placeholder
                            "status": "supported",
                            "confidence": 0.9,
                            "reasoning": "Strong evidence",
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        eval_events = [e for e in events if isinstance(e, HypothesisEvaluated)]
        assert len(eval_events) == 1
        assert eval_events[0].status == "supported"

    @pytest.mark.asyncio
    async def test_record_negative_control(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "record_negative_control",
                        {"smiles": "CCO", "name": "Ethanol", "prediction_score": 0.1},
                    ),
                ],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        assert len(investigation.negative_controls) == 1
        assert investigation.negative_controls[0].correctly_classified is True
        nc_events = [e for e in events if isinstance(e, NegativeControlRecorded)]
        assert len(nc_events) == 1

    @pytest.mark.asyncio
    async def test_conclude_ends_loop(self, mock_client: AsyncMock, registry: ToolRegistry) -> None:
        mock_client.create_message.side_effect = [
            _make_response(
                content=[
                    _tool_use_block(
                        "tu_1",
                        "conclude_investigation",
                        {
                            "summary": "Found 3 candidates",
                            "candidates": [
                                {"smiles": "CCO", "name": "ethanol"},
                                {"smiles": "c1ccccc1", "name": "benzene"},
                            ],
                            "citations": ["Doe 2024"],
                        },
                    ),
                ],
                stop_reason="tool_use",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=50)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        assert investigation.summary == "Found 3 candidates"
        assert len(investigation.candidates) == 2
        assert investigation.candidates[0].smiles == "CCO"
        assert investigation.candidates[0].rank == 1
        assert len(investigation.citations) == 1
        completed = [e for e in events if isinstance(e, InvestigationCompleted)]
        assert len(completed) == 1
        assert completed[0].candidate_count == 2


class TestOrchestratorMaxIterations:
    @pytest.mark.asyncio
    async def test_stops_at_max_iterations(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.return_value = _make_response(
            content=[
                _text_block("Thinking..."),
                _tool_use_block("tu_1", "validate_smiles", {"smiles": "CCO"}),
            ],
            stop_reason="tool_use",
        )
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=3)
        investigation = Investigation(prompt="Test")

        await _collect_events(orchestrator, investigation)

        assert mock_client.create_message.call_count == 3
        assert investigation.status == InvestigationStatus.COMPLETED


class TestOrchestratorErrorHandling:
    @pytest.mark.asyncio
    async def test_api_error_emits_error_event(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        mock_client.create_message.side_effect = RuntimeError("API down")
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        error_events = [e for e in events if isinstance(e, InvestigationError)]
        assert len(error_events) == 1
        assert "API down" in error_events[0].error
        assert investigation.status == InvestigationStatus.FAILED

    @pytest.mark.asyncio
    async def test_tool_error_returns_error_json(
        self, mock_client: AsyncMock, registry: ToolRegistry
    ) -> None:
        async def failing_tool(query: str) -> str:
            """A tool that fails."""
            raise ValueError("Bad input")

        registry.register("failing_tool", failing_tool)
        mock_client.create_message.side_effect = [
            _make_response(
                content=[_tool_use_block("tu_1", "failing_tool", {"query": "test"})],
                stop_reason="tool_use",
            ),
            _make_response(
                content=[_text_block("Done.")],
                stop_reason="end_turn",
            ),
        ]
        orchestrator = Orchestrator(client=mock_client, registry=registry, max_iterations=5)
        investigation = Investigation(prompt="Test")

        events = await _collect_events(orchestrator, investigation)

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) == 1
        assert "error" in tool_results[0].result_preview.lower()
        assert investigation.status == InvestigationStatus.COMPLETED

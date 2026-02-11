from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.events import (
    ExperimentCompleted,
    ExperimentStarted,
    FindingRecorded,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    NegativeControlRecorded,
    OutputSummarized,
    ToolCalled,
    ToolResultEvent,
)
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus


@dataclass(frozen=True)
class FakeResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int


def _make_text_response(text: str) -> FakeResponse:
    return FakeResponse(
        content=[{"type": "text", "text": text}],
        stop_reason="end_turn",
        input_tokens=100,
        output_tokens=50,
    )


def _make_tool_use_response(
    tool_name: str, tool_input: dict[str, Any], tool_id: str = "tool_1"
) -> FakeResponse:
    return FakeResponse(
        content=[
            {"type": "text", "text": "Reasoning..."},
            {"type": "tool_use", "id": tool_id, "name": tool_name, "input": tool_input},
        ],
        stop_reason="tool_use",
        input_tokens=100,
        output_tokens=50,
    )


def _formulation_json() -> str:
    return json.dumps(
        {
            "hypotheses": [
                {
                    "statement": "Thiazolidine compounds inhibit MRSA PBP2a",
                    "rationale": "Literature suggests beta-lactam analogs bind PBP2a",
                },
            ],
            "negative_controls": [
                {"smiles": "CCO", "name": "Ethanol", "source": "known inactive"},
            ],
        }
    )


def _experiment_design_json() -> str:
    return json.dumps(
        {
            "description": "Dock thiazolidine analogs against PBP2a",
            "tool_plan": ["search_literature", "validate_smiles"],
            "success_criteria": "Docking score < -8.0 kcal/mol",
            "failure_criteria": "No compounds with score < -6.0",
        }
    )


def _evaluation_json(status: str = "supported") -> str:
    return json.dumps(
        {
            "status": status,
            "confidence": 0.85,
            "reasoning": "Strong binding evidence from docking",
        }
    )


def _revision_evaluation_json() -> str:
    return json.dumps(
        {
            "status": "revised",
            "confidence": 0.4,
            "reasoning": "Partial evidence, need narrower scope",
            "revision": "Thiazolidine with 4-chloro substitution specifically inhibits PBP2a",
        }
    )


def _synthesis_json() -> str:
    return json.dumps(
        {
            "summary": "Investigation found 1 promising candidate via PBP2a docking.",
            "candidates": [
                {
                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                    "name": "Thiazolidine-A1",
                    "rationale": "Strong PBP2a binding",
                    "rank": 1,
                }
            ],
            "citations": ["10.1234/test"],
        }
    )


def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    async def search_literature(query: str) -> str:
        """Search papers. Args: query: search query"""
        return '{"results": [{"title": "Test paper", "doi": "10.1234/test"}]}'

    async def validate_smiles(smiles: str) -> str:
        """Validate SMILES. Args: smiles: s"""
        return json.dumps({"smiles": smiles, "valid": True})

    async def record_finding(
        title: str,
        detail: str,
        hypothesis_id: str = "",
        evidence_type: str = "neutral",
        evidence: str = "",
    ) -> str:
        """Record a finding."""
        return json.dumps({"status": "recorded", "title": title})

    async def record_negative_control(
        smiles: str, name: str, prediction_score: float = 0.0, source: str = ""
    ) -> str:
        """Record negative control."""
        return json.dumps({"status": "recorded", "smiles": smiles})

    registry.register("search_literature", search_literature)
    registry.register("validate_smiles", validate_smiles)
    registry.register("record_finding", record_finding)
    registry.register("record_negative_control", record_negative_control)
    return registry


def _make_clients() -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    director = AsyncMock()
    director.model = "claude-opus-4-6"

    researcher = AsyncMock()
    researcher.model = "claude-sonnet-4-5-20250929"

    summarizer = AsyncMock()
    summarizer.model = "claude-haiku-4-5-20251001"

    return director, researcher, summarizer


class TestHypothesisFormulation:
    @pytest.mark.asyncio
    async def test_director_creates_hypotheses(self) -> None:
        director, researcher, summarizer = _make_clients()

        # Director: formulation, experiment design, evaluation, synthesis
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        # Researcher: literature survey (end_turn), experiment execution (end_turn)
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Find antimicrobials for MRSA")
        events = [e async for e in orchestrator.run(investigation)]

        hyp_events = [e for e in events if isinstance(e, HypothesisFormulated)]
        assert len(hyp_events) == 1
        assert "Thiazolidine" in hyp_events[0].statement
        assert len(investigation.hypotheses) == 1


class TestExperimentExecution:
    @pytest.mark.asyncio
    async def test_researcher_calls_tools_during_experiment(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        # Literature survey: end_turn. Experiment: tool call then end_turn.
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_text_response("Literature done."),
                _make_tool_use_response("search_literature", {"query": "MRSA PBP2a"}),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=5,
        )

        investigation = Investigation(prompt="Find antimicrobials")
        events = [e async for e in orchestrator.run(investigation)]

        tool_called = [e for e in events if isinstance(e, ToolCalled)]
        assert len(tool_called) >= 1
        assert tool_called[0].tool_name == "search_literature"

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) >= 1

    @pytest.mark.asyncio
    async def test_experiment_started_and_completed_events(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        started = [e for e in events if isinstance(e, ExperimentStarted)]
        completed = [e for e in events if isinstance(e, ExperimentCompleted)]
        assert len(started) == 1
        assert "Dock thiazolidine" in started[0].description
        assert len(completed) == 1
        assert len(investigation.experiments) == 1

    @pytest.mark.asyncio
    async def test_researcher_records_finding_linked_to_hypothesis(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        # Literature: end_turn. Experiment: record_finding then end_turn.
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_text_response("Lit done."),
                _make_tool_use_response(
                    "record_finding",
                    {
                        "title": "Binding confirmed",
                        "detail": "Docking score -9.2",
                        "hypothesis_id": "will_be_set_by_prompt",
                        "evidence_type": "supporting",
                    },
                ),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=5,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        finding_events = [e for e in events if isinstance(e, FindingRecorded)]
        assert len(finding_events) == 1
        assert finding_events[0].title == "Binding confirmed"
        assert finding_events[0].evidence_type == "supporting"
        assert len(investigation.findings) == 1


class TestHypothesisEvaluation:
    @pytest.mark.asyncio
    async def test_director_evaluates_hypothesis(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json("supported")),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        eval_events = [e for e in events if isinstance(e, HypothesisEvaluated)]
        assert len(eval_events) == 1
        assert eval_events[0].status == "supported"
        assert eval_events[0].confidence == 0.85

    @pytest.mark.asyncio
    async def test_revised_hypothesis_adds_new_to_queue(self) -> None:
        director, researcher, summarizer = _make_clients()

        # formulation, design#1, evaluate#1 (revised), design#2, evaluate#2, synthesis
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_revision_evaluation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json("supported")),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        hyp_events = [e for e in events if isinstance(e, HypothesisFormulated)]
        # Original + revised
        assert len(hyp_events) == 2
        assert hyp_events[1].parent_id != ""
        assert len(investigation.hypotheses) == 2


class TestNegativeControls:
    @pytest.mark.asyncio
    async def test_negative_controls_from_formulation(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        nc_events = [e for e in events if isinstance(e, NegativeControlRecorded)]
        assert len(nc_events) == 1
        assert nc_events[0].smiles == "CCO"
        assert nc_events[0].name == "Ethanol"
        assert len(investigation.negative_controls) == 1


class TestSummarizerCompression:
    @pytest.mark.asyncio
    async def test_large_output_is_summarized(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        large_output = "x" * 3000

        async def big_tool(query: str) -> str:
            """Search papers."""
            return large_output

        registry = _build_registry()
        registry.register("search_literature", big_tool)

        # Literature: tool call then end_turn. Experiment: end_turn.
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "test"}),
                _make_text_response("Lit done."),
                _make_text_response("Experiment done."),
            ]
        )
        summarizer.create_message = AsyncMock(
            return_value=_make_text_response("Compressed output.")
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_experiment=5,
            summarizer_threshold=2000,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        summarized = [e for e in events if isinstance(e, OutputSummarized)]
        assert len(summarized) == 1
        assert summarized[0].original_length == 3000
        assert summarized[0].tool_name == "search_literature"

    @pytest.mark.asyncio
    async def test_small_output_not_summarized(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "test"}),
                _make_text_response("Lit done."),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=5,
            summarizer_threshold=2000,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        summarized = [e for e in events if isinstance(e, OutputSummarized)]
        assert len(summarized) == 0
        summarizer.create_message.assert_not_called()


class TestDirectorSynthesis:
    @pytest.mark.asyncio
    async def test_synthesis_populates_investigation(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        assert investigation.status == InvestigationStatus.COMPLETED
        assert "promising candidate" in investigation.summary
        assert len(investigation.candidates) == 1
        assert investigation.candidates[0].smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert len(investigation.citations) == 1

        completed = [e for e in events if isinstance(e, InvestigationCompleted)]
        assert len(completed) == 1
        assert completed[0].candidate_count == 1
        assert len(completed[0].candidates) == 1
        assert len(completed[0].hypotheses) == 1
        assert len(completed[0].negative_controls) == 1


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_complete_flow_event_types(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "MRSA"}),
                _make_text_response("Lit done."),
                _make_tool_use_response("validate_smiles", {"smiles": "CCO"}),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=5,
        )

        investigation = Investigation(prompt="Find antimicrobials for MRSA")
        events = [e async for e in orchestrator.run(investigation)]

        event_types = {type(e).__name__ for e in events}
        assert "HypothesisFormulated" in event_types
        assert "ExperimentStarted" in event_types
        assert "ExperimentCompleted" in event_types
        assert "HypothesisEvaluated" in event_types
        assert "NegativeControlRecorded" in event_types
        assert "Thinking" in event_types
        assert "ToolCalled" in event_types
        assert "ToolResultEvent" in event_types
        assert "InvestigationCompleted" in event_types


class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_two_hypotheses_run_in_parallel_batch(self) -> None:
        director, researcher, summarizer = _make_clients()

        two_hyp_formulation = json.dumps(
            {
                "hypotheses": [
                    {"statement": "Hypothesis A", "rationale": "Reason A"},
                    {"statement": "Hypothesis B", "rationale": "Reason B"},
                ],
                "negative_controls": [],
            }
        )

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(two_hyp_formulation),
                _make_text_response(_experiment_design_json()),  # design A
                _make_text_response(_experiment_design_json()),  # design B
                _make_text_response(_evaluation_json()),  # eval A
                _make_text_response(_evaluation_json()),  # eval B
                _make_text_response(_synthesis_json()),
            ]
        )
        researcher.create_message = AsyncMock(
            return_value=_make_text_response("Done.")
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test parallel")
        events = [e async for e in orchestrator.run(investigation)]

        # Both hypotheses should be tested
        started = [e for e in events if isinstance(e, ExperimentStarted)]
        assert len(started) == 2
        completed = [e for e in events if isinstance(e, ExperimentCompleted)]
        assert len(completed) == 2
        evaluated = [e for e in events if isinstance(e, HypothesisEvaluated)]
        assert len(evaluated) == 2
        assert investigation.status == InvestigationStatus.COMPLETED


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_director_api_error(self) -> None:
        director, researcher, summarizer = _make_clients()
        director.create_message = AsyncMock(side_effect=RuntimeError("API down"))
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        error_events = [e for e in events if isinstance(e, InvestigationError)]
        assert len(error_events) == 1
        assert "API down" in error_events[0].error
        assert investigation.status == InvestigationStatus.FAILED

    @pytest.mark.asyncio
    async def test_researcher_tool_error_handled_gracefully(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_formulation_json()),
                _make_text_response(_experiment_design_json()),
                _make_text_response(_evaluation_json()),
                _make_text_response(_synthesis_json()),
            ]
        )
        # Literature: end_turn. Experiment: unknown tool then end_turn.
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_text_response("Lit done."),
                _make_tool_use_response("unknown_tool", {"arg": "val"}),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=5,
        )

        investigation = Investigation(prompt="Test")
        async for _ in orchestrator.run(investigation):
            pass

        # Should still complete (tool error returns error JSON, doesn't crash)
        assert investigation.status == InvestigationStatus.COMPLETED

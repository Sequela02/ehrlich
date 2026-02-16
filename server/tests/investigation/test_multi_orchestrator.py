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
    HypothesisTreeUpdated,
    InvestigationCompleted,
    InvestigationError,
    NegativeControlRecorded,
    OutputSummarized,
    Thinking,
    ToolCalled,
    ToolResultEvent,
    ValidationMetricsComputed,
)
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus


@dataclass(frozen=True)
class FakeResponse:
    content: list[dict[str, Any]]
    stop_reason: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_write_input_tokens: int = 0


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


def _make_director_side_effect(*text_responses: str):
    """Return a callable async generator that yields stream events for successive calls."""
    call_idx = 0

    async def _stream(**kwargs: Any):
        nonlocal call_idx
        text = text_responses[call_idx]
        call_idx += 1
        yield {"type": "text", "text": text}
        yield {
            "type": "result",
            "response": FakeResponse(
                content=[{"type": "text", "text": text}],
                stop_reason="end_turn",
                input_tokens=100,
                output_tokens=50,
            ),
        }

    return _stream


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
                {"identifier": "CCO", "name": "Ethanol", "source": "known inactive"},
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
            "certainty_of_evidence": "moderate",
            "evidence_convergence": "converging",
            "reasoning": "Strong binding evidence from docking",
            "key_evidence": ["Docking score -9.2 kcal/mol (tier 7)"],
            "action": "prune",
        }
    )


def _revision_evaluation_json() -> str:
    return json.dumps(
        {
            "status": "revised",
            "confidence": 0.4,
            "certainty_of_evidence": "low",
            "evidence_convergence": "mixed",
            "reasoning": "Partial evidence, need narrower scope",
            "key_evidence": ["Some binding but weak (tier 7)"],
            "action": "branch",
            "revision": "Thiazolidine with 4-chloro substitution specifically inhibits PBP2a",
        }
    )


def _deepen_evaluation_json() -> str:
    return json.dumps(
        {
            "status": "revised",
            "confidence": 0.6,
            "certainty_of_evidence": "moderate",
            "evidence_convergence": "mixed",
            "reasoning": "Promising but needs narrower scope",
            "key_evidence": ["Moderate binding (tier 5)"],
            "action": "deepen",
            "revision": "Thiazolidine analogs with MW < 300 selectively inhibit PBP2a",
        }
    )


def _synthesis_json() -> str:
    return json.dumps(
        {
            "summary": "Investigation found 1 promising candidate via PBP2a docking.",
            "candidates": [
                {
                    "identifier": "CC(=O)Oc1ccccc1C(=O)O",
                    "identifier_type": "smiles",
                    "name": "Thiazolidine-A1",
                    "rationale": "Strong PBP2a binding",
                    "rank": 1,
                    "scores": {},
                    "attributes": {},
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
        identifier: str, name: str, score: float = 0.0, source: str = ""
    ) -> str:
        """Record negative control."""
        return json.dumps({"status": "recorded", "identifier": identifier})

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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        )
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json("supported"),
            _synthesis_json(),
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
        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _revision_evaluation_json(),
            _experiment_design_json(),
            _evaluation_json("supported"),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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
        assert nc_events[0].identifier == "CCO"
        assert nc_events[0].name == "Ethanol"
        assert len(investigation.negative_controls) == 1


class TestValidationMetrics:
    @pytest.mark.asyncio
    async def test_phase5_emits_validation_metrics(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test validation")
        events = [e async for e in orchestrator.run(investigation)]

        vm_events = [e for e in events if isinstance(e, ValidationMetricsComputed)]
        assert len(vm_events) == 1
        assert vm_events[0].investigation_id == investigation.id

    @pytest.mark.asyncio
    async def test_phase5_captures_model_id(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        )

        # Researcher calls train_model, returns a model_id
        train_result = json.dumps({"model_id": "xgboost_test_abc12345", "metrics": {}})

        async def mock_train_model(target: str = "", **kwargs: Any) -> str:
            """Train model."""
            return train_result

        registry = _build_registry()
        registry.register("train_model", mock_train_model)

        researcher.create_message = AsyncMock(
            side_effect=[
                _make_text_response("Lit done."),
                _make_tool_use_response("train_model", {"target": "test"}),
                _make_text_response("Experiment done."),
            ]
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_experiment=5,
        )

        investigation = Investigation(prompt="Test model capture")
        async for _ in orchestrator.run(investigation):
            pass

        assert "xgboost_test_abc12345" in investigation.trained_model_ids

    @pytest.mark.asyncio
    async def test_completed_event_has_validation_metrics(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        completed = [e for e in events if isinstance(e, InvestigationCompleted)]
        assert len(completed) == 1
        assert "z_prime" in completed[0].validation_metrics
        assert "z_prime_quality" in completed[0].validation_metrics


class TestSummarizerCompression:
    @pytest.mark.asyncio
    async def test_large_output_is_summarized(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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
        assert investigation.candidates[0].identifier == "CC(=O)Oc1ccccc1C(=O)O"
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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

        director.stream_message = _make_director_side_effect(
            two_hyp_formulation,
            _experiment_design_json(),  # design A
            _experiment_design_json(),  # design B
            _evaluation_json(),  # eval A
            _evaluation_json(),  # eval B
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

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

        async def _failing_stream(**kwargs: Any):
            raise RuntimeError("API down")
            yield  # noqa: RUF027 -- makes this an async generator

        director.stream_message = _failing_stream
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

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
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


class TestExtendedThinking:
    @pytest.mark.asyncio
    async def test_thinking_blocks_emitted_as_events(self) -> None:
        director, researcher, summarizer = _make_clients()

        call_idx = 0
        responses = [
            (_formulation_json(), "Let me analyze..."),
            (_experiment_design_json(), ""),
            (_evaluation_json(), ""),
            (_synthesis_json(), ""),
        ]

        async def _stream_with_thinking(**kwargs: Any):
            nonlocal call_idx
            text, thinking = responses[call_idx]
            call_idx += 1
            if thinking:
                yield {"type": "thinking", "text": thinking}
            yield {"type": "text", "text": text}
            yield {
                "type": "result",
                "response": FakeResponse(
                    content=[{"type": "text", "text": text}],
                    stop_reason="end_turn",
                    input_tokens=100,
                    output_tokens=50,
                ),
            }

        director.stream_message = _stream_with_thinking
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test thinking")
        events = [e async for e in orchestrator.run(investigation)]

        thinking_events = [e for e in events if isinstance(e, Thinking)]
        director_thinking = [t for t in thinking_events if "Let me analyze" in t.text]
        assert len(director_thinking) == 1


class TestToolChoice:
    @pytest.mark.asyncio
    async def test_researcher_first_turn_forces_tool_use(self) -> None:
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test tool_choice")
        async for _ in orchestrator.run(investigation):
            pass

        # First researcher call (literature survey) should use tool_choice={"type": "any"}
        first_call_kwargs = researcher.create_message.call_args_list[0]
        assert first_call_kwargs.kwargs.get("tool_choice") == {"type": "any"}


class TestStructuredOutputs:
    @pytest.mark.asyncio
    async def test_director_calls_pass_output_config(self) -> None:
        """Verify that _director_call passes output_config to stream_message."""
        director, researcher, summarizer = _make_clients()

        captured_kwargs: list[dict[str, Any]] = []

        call_idx = 0
        texts = [
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        ]

        async def _capturing_stream(**kwargs: Any):
            nonlocal call_idx
            captured_kwargs.append(kwargs)
            text = texts[call_idx]
            call_idx += 1
            yield {"type": "text", "text": text}
            yield {
                "type": "result",
                "response": FakeResponse(
                    content=[{"type": "text", "text": text}],
                    stop_reason="end_turn",
                    input_tokens=100,
                    output_tokens=50,
                ),
            }

        director.stream_message = _capturing_stream
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test structured outputs")
        async for _ in orchestrator.run(investigation):
            pass

        assert investigation.status == InvestigationStatus.COMPLETED
        # All 4 director calls should have output_config set
        assert len(captured_kwargs) == 4
        for kw in captured_kwargs:
            assert kw.get("output_config") is not None
            assert kw["output_config"]["format"]["type"] == "json_schema"


class TestTreeSearch:
    @pytest.mark.asyncio
    async def test_tree_search_deepens_promising_hypothesis(self) -> None:
        """Director returns action=deepen, new sub-hypothesis created at depth 1."""
        director, researcher, summarizer = _make_clients()

        # formulation, design#1, eval#1 (deepen), design#2, eval#2 (prune), synthesis
        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _deepen_evaluation_json(),
            _experiment_design_json(),
            _evaluation_json("supported"),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test tree deepen")
        events = [e async for e in orchestrator.run(investigation)]

        # Original + deepened child
        hyp_events = [e for e in events if isinstance(e, HypothesisFormulated)]
        assert len(hyp_events) == 2

        # Child should have parent_id set
        child_event = hyp_events[1]
        assert child_event.parent_id != ""

        # Check tree updated events
        tree_events = [e for e in events if isinstance(e, HypothesisTreeUpdated)]
        assert len(tree_events) >= 1

        deepen_events = [e for e in tree_events if e.action == "deepen"]
        assert len(deepen_events) == 1
        assert deepen_events[0].children_count == 1

        # Child hypothesis should be at depth 1
        assert len(investigation.hypotheses) == 2
        child = investigation.hypotheses[1]
        assert child.depth == 1
        assert child.parent_id == investigation.hypotheses[0].id

    @pytest.mark.asyncio
    async def test_tree_search_prunes_refuted_hypothesis(self) -> None:
        """Director returns action=prune, hypothesis not re-tested."""
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json("refuted"),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test tree prune")
        events = [e async for e in orchestrator.run(investigation)]

        tree_events = [e for e in events if isinstance(e, HypothesisTreeUpdated)]
        assert len(tree_events) == 1
        assert tree_events[0].action == "prune"

        # Only 1 hypothesis (original), no children created
        assert len(investigation.hypotheses) == 1
        assert investigation.hypotheses[0].status.value == "refuted"

    @pytest.mark.asyncio
    async def test_tree_search_respects_max_depth(self) -> None:
        """Hypotheses at max_depth are not further deepened."""
        from ehrlich.investigation.application.tree_manager import TreeManager

        director, researcher, summarizer = _make_clients()

        # With max_depth=1: formulate root (depth=0), test it, deepen to depth=1,
        # test child, try to deepen again but depth=1 is at max, so prune instead.
        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _deepen_evaluation_json(),
            _experiment_design_json(),
            _evaluation_json("supported"),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        tree_manager = TreeManager(max_depth=1)
        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
            tree_manager=tree_manager,
        )

        investigation = Investigation(prompt="Test max depth")
        async for _ in orchestrator.run(investigation):
            pass

        # Root tested and deepened, child tested but cannot deepen further
        assert len(investigation.hypotheses) == 2
        # Child at depth 1 (which == max_depth) should not produce more children
        child = investigation.hypotheses[1]
        assert child.depth == 1
        assert len(child.children) == 0

    @pytest.mark.asyncio
    async def test_tree_events_have_investigation_id(self) -> None:
        """All HypothesisTreeUpdated events include investigation_id."""
        director, researcher, summarizer = _make_clients()

        director.stream_message = _make_director_side_effect(
            _formulation_json(),
            _experiment_design_json(),
            _evaluation_json(),
            _synthesis_json(),
        )
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_experiment=1,
        )

        investigation = Investigation(prompt="Test tree events")
        events = [e async for e in orchestrator.run(investigation)]

        tree_events = [e for e in events if isinstance(e, HypothesisTreeUpdated)]
        assert len(tree_events) >= 1
        for te in tree_events:
            assert te.investigation_id == investigation.id

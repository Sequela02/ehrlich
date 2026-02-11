from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.events import (
    DirectorDecision,
    DirectorPlanning,
    FindingRecorded,
    InvestigationCompleted,
    InvestigationError,
    OutputSummarized,
    PhaseStarted,
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


def _plan_json() -> str:
    import json

    return json.dumps(
        {
            "phases": [
                {
                    "name": "Literature Review",
                    "goals": ["Find antimicrobials"],
                    "key_questions": ["What works?"],
                }
            ],
            "focus_areas": ["MRSA"],
            "success_criteria": ["Find candidates"],
        }
    )


def _review_json(proceed: bool = True) -> str:
    import json

    return json.dumps(
        {
            "quality_score": 0.8,
            "key_findings": ["Found something"],
            "gaps": [],
            "proceed": proceed,
            "next_phase_guidance": "Continue",
        }
    )


def _synthesis_json() -> str:
    import json

    return json.dumps(
        {
            "summary": "Investigation found 2 promising candidates.",
            "candidates": [
                {
                    "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                    "name": "Aspirin analog",
                    "rationale": "Good binding",
                    "rank": 1,
                }
            ],
            "citations": ["10.1234/test"],
            "confidence": "medium",
            "limitations": ["Limited data"],
        }
    )


def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    async def search_literature(query: str) -> str:
        """Search papers. Args: query: search query"""
        return '{"results": [{"title": "Test paper", "doi": "10.1234/test"}]}'

    async def record_finding(title: str, detail: str, phase: str = "", evidence: str = "") -> str:
        """Record a finding. Args: title: t detail: d"""
        return '{"status": "recorded"}'

    registry.register("search_literature", search_literature)
    registry.register("record_finding", record_finding)
    return registry


class TestDirectorPlanning:
    @pytest.mark.asyncio
    async def test_yields_planning_events(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(return_value=_make_text_response(_plan_json()))

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=1,
        )

        # Director: plan + review + synthesis = 3 calls
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        investigation = Investigation(prompt="Find antimicrobials for MRSA")
        events = [e async for e in orchestrator.run(investigation)]

        planning_events = [e for e in events if isinstance(e, DirectorPlanning)]
        assert len(planning_events) >= 2  # planning + review + synthesis
        assert planning_events[0].stage == "planning"

    @pytest.mark.asyncio
    async def test_yields_director_decision(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=1,
        )

        investigation = Investigation(prompt="Find antimicrobials")
        events = [e async for e in orchestrator.run(investigation)]

        decisions = [e for e in events if isinstance(e, DirectorDecision)]
        assert len(decisions) >= 2
        assert decisions[0].stage == "planning"
        assert "phases" in decisions[0].decision


class TestResearcherPhaseExecution:
    @pytest.mark.asyncio
    async def test_researcher_calls_tools(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "MRSA antimicrobials"}),
                _make_text_response("Phase done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=5,
        )

        investigation = Investigation(prompt="Find antimicrobials for MRSA")
        events = [e async for e in orchestrator.run(investigation)]

        tool_called = [e for e in events if isinstance(e, ToolCalled)]
        assert len(tool_called) >= 1
        assert tool_called[0].tool_name == "search_literature"

        tool_results = [e for e in events if isinstance(e, ToolResultEvent)]
        assert len(tool_results) >= 1

    @pytest.mark.asyncio
    async def test_researcher_records_finding(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response(
                    "record_finding", {"title": "Key insight", "detail": "Details here"}
                ),
                _make_text_response("Done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=5,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        finding_events = [e for e in events if isinstance(e, FindingRecorded)]
        assert len(finding_events) == 1
        assert finding_events[0].title == "Key insight"
        assert len(investigation.findings) == 1


class TestSummarizerCompression:
    @pytest.mark.asyncio
    async def test_large_output_is_summarized(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        large_output = "x" * 3000

        async def big_tool(query: str) -> str:
            """Search papers. Args: query: q"""
            return large_output

        registry = ToolRegistry()
        registry.register("search_literature", big_tool)

        async def mock_record(title: str, detail: str, phase: str = "", evidence: str = "") -> str:
            """Record. Args: title: t detail: d"""
            return '{"status": "ok"}'

        registry.register("record_finding", mock_record)

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "test"}),
                _make_text_response("Done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"
        summarizer.create_message = AsyncMock(
            return_value=_make_text_response("Compressed output.")
        )

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=registry,
            max_iterations_per_phase=5,
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
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "test"}),
                _make_text_response("Done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=5,
            summarizer_threshold=2000,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        summarized = [e for e in events if isinstance(e, OutputSummarized)]
        assert len(summarized) == 0
        # Summarizer should not have been called
        summarizer.create_message.assert_not_called()


class TestDirectorReview:
    @pytest.mark.asyncio
    async def test_review_stop_on_no_proceed(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json(proceed=False)),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        # Should have only 1 phase since review said proceed=false
        phase_events = [e for e in events if isinstance(e, PhaseStarted)]
        assert len(phase_events) == 1


class TestDirectorSynthesis:
    @pytest.mark.asyncio
    async def test_synthesis_populates_investigation(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(return_value=_make_text_response("Done."))

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=1,
        )

        investigation = Investigation(prompt="Test")
        events = [e async for e in orchestrator.run(investigation)]

        assert investigation.status == InvestigationStatus.COMPLETED
        assert "promising candidates" in investigation.summary
        assert len(investigation.candidates) == 1
        assert investigation.candidates[0].smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert len(investigation.citations) == 1

        completed = [e for e in events if isinstance(e, InvestigationCompleted)]
        assert len(completed) == 1
        assert completed[0].candidate_count == 1
        assert len(completed[0].candidates) == 1


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_complete_flow_events(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("search_literature", {"query": "MRSA"}),
                _make_text_response("Phase done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=5,
        )

        investigation = Investigation(prompt="Find antimicrobials for MRSA")
        events = [e async for e in orchestrator.run(investigation)]

        event_types = [type(e).__name__ for e in events]
        assert "DirectorPlanning" in event_types
        assert "DirectorDecision" in event_types
        assert "PhaseStarted" in event_types
        assert "Thinking" in event_types
        assert "ToolCalled" in event_types
        assert "ToolResultEvent" in event_types
        assert "InvestigationCompleted" in event_types


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_director_api_error(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(side_effect=RuntimeError("API down"))

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

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
    async def test_researcher_tool_error(self) -> None:
        director = AsyncMock()
        director.model = "claude-opus-4-6"
        director.create_message = AsyncMock(
            side_effect=[
                _make_text_response(_plan_json()),
                _make_text_response(_review_json()),
                _make_text_response(_synthesis_json()),
            ]
        )

        researcher = AsyncMock()
        researcher.model = "claude-sonnet-4-5-20250929"
        researcher.create_message = AsyncMock(
            side_effect=[
                _make_tool_use_response("unknown_tool", {"arg": "val"}),
                _make_text_response("Done."),
            ]
        )

        summarizer = AsyncMock()
        summarizer.model = "claude-haiku-4-5-20251001"

        orchestrator = MultiModelOrchestrator(
            director=director,
            researcher=researcher,
            summarizer=summarizer,
            registry=_build_registry(),
            max_iterations_per_phase=5,
        )

        investigation = Investigation(prompt="Test")
        async for _ in orchestrator.run(investigation):
            pass

        # Should still complete (tool error returns error JSON, doesn't crash)
        assert investigation.status == InvestigationStatus.COMPLETED

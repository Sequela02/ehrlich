from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.investigation.domain.events import (
    DomainEvent,
    FindingRecorded,
    InvestigationCompleted,
    InvestigationError,
    PhaseStarted,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)


class TestDomainEventToSSE:
    def test_phase_started(self) -> None:
        event = PhaseStarted(phase="Literature Review", investigation_id="inv-1")
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.PHASE_STARTED
        assert sse.data["phase"] == "Literature Review"

    def test_tool_called(self) -> None:
        event = ToolCalled(
            tool_name="search_literature",
            tool_input={"query": "MRSA"},
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.TOOL_CALLED
        assert sse.data["tool_name"] == "search_literature"

    def test_tool_result(self) -> None:
        event = ToolResultEvent(
            tool_name="search_literature",
            result_preview='{"count": 5}',
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.TOOL_RESULT

    def test_finding_recorded(self) -> None:
        event = FindingRecorded(
            title="Key insight",
            detail="Important detail",
            phase="Data Exploration",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.FINDING_RECORDED
        assert sse.data["title"] == "Key insight"

    def test_thinking(self) -> None:
        event = Thinking(text="Let me analyze this...", investigation_id="inv-1")
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.THINKING

    def test_error(self) -> None:
        event = InvestigationError(error="API timeout", investigation_id="inv-1")
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.ERROR
        assert sse.data["error"] == "API timeout"

    def test_completed(self) -> None:
        event = InvestigationCompleted(
            investigation_id="inv-1",
            candidate_count=3,
            summary="Found candidates",
            cost={"total_cost_usd": 0.05},
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.COMPLETED
        assert sse.data["candidate_count"] == 3
        assert sse.data["cost"]["total_cost_usd"] == 0.05

    def test_unknown_event_returns_none(self) -> None:
        event = DomainEvent()
        sse = domain_event_to_sse(event)
        assert sse is None

    def test_sse_format_is_json(self) -> None:
        event = PhaseStarted(phase="Test", investigation_id="inv-1")
        sse = domain_event_to_sse(event)
        assert sse is not None
        formatted = sse.format()
        import json

        parsed = json.loads(formatted)
        assert parsed["event"] == "phase_started"
        assert parsed["data"]["phase"] == "Test"

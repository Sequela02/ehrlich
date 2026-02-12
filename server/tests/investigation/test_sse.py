from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.investigation.domain.events import (
    CostUpdate,
    DomainEvent,
    ExperimentCompleted,
    ExperimentStarted,
    FindingRecorded,
    HypothesisApprovalRequested,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    NegativeControlRecorded,
    PhaseChanged,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)


class TestDomainEventToSSE:
    def test_hypothesis_formulated(self) -> None:
        event = HypothesisFormulated(
            hypothesis_id="h1",
            statement="Test hypothesis",
            rationale="Based on evidence",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.HYPOTHESIS_FORMULATED
        assert sse.data["hypothesis_id"] == "h1"
        assert sse.data["statement"] == "Test hypothesis"

    def test_experiment_started(self) -> None:
        event = ExperimentStarted(
            experiment_id="e1",
            hypothesis_id="h1",
            description="Test binding",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.EXPERIMENT_STARTED
        assert sse.data["experiment_id"] == "e1"

    def test_experiment_completed(self) -> None:
        event = ExperimentCompleted(
            experiment_id="e1",
            hypothesis_id="h1",
            tool_count=5,
            finding_count=2,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.EXPERIMENT_COMPLETED
        assert sse.data["tool_count"] == 5

    def test_hypothesis_evaluated(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="supported",
            confidence=0.85,
            reasoning="Strong evidence",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.HYPOTHESIS_EVALUATED
        assert sse.data["confidence"] == 0.85

    def test_negative_control(self) -> None:
        event = NegativeControlRecorded(
            identifier="CCO",
            identifier_type="smiles",
            name="Ethanol",
            score=0.1,
            correctly_classified=True,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.NEGATIVE_CONTROL
        assert sse.data["correctly_classified"] is True

    def test_tool_called(self) -> None:
        event = ToolCalled(
            tool_name="search_literature",
            tool_input={"query": "MRSA"},
            experiment_id="exp-1",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.TOOL_CALLED
        assert sse.data["tool_name"] == "search_literature"
        assert sse.data["experiment_id"] == "exp-1"

    def test_tool_result(self) -> None:
        event = ToolResultEvent(
            tool_name="search_literature",
            result_preview='{"count": 5}',
            experiment_id="exp-1",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.TOOL_RESULT
        assert sse.data["experiment_id"] == "exp-1"

    def test_finding_recorded(self) -> None:
        event = FindingRecorded(
            title="Key insight",
            detail="Important detail",
            hypothesis_id="h1",
            evidence_type="supporting",
            source_type="chembl",
            source_id="CHEMBL25",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.FINDING_RECORDED
        assert sse.data["title"] == "Key insight"
        assert sse.data["hypothesis_id"] == "h1"
        assert sse.data["evidence_type"] == "supporting"
        assert sse.data["source_type"] == "chembl"
        assert sse.data["source_id"] == "CHEMBL25"

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
            hypotheses=[{"id": "h1", "status": "supported"}],
            negative_controls=[{"name": "Ethanol", "correctly_classified": True}],
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.COMPLETED
        assert sse.data["candidate_count"] == 3
        assert sse.data["cost"]["total_cost_usd"] == 0.05
        assert len(sse.data["hypotheses"]) == 1
        assert len(sse.data["negative_controls"]) == 1

    def test_phase_changed(self) -> None:
        event = PhaseChanged(
            phase=2,
            name="Formulation",
            description="Director formulating hypotheses",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.PHASE_CHANGED
        assert sse.data["phase"] == 2
        assert sse.data["name"] == "Formulation"
        assert sse.data["description"] == "Director formulating hypotheses"

    def test_cost_update(self) -> None:
        event = CostUpdate(
            input_tokens=5000,
            output_tokens=1000,
            total_tokens=6000,
            total_cost_usd=0.1275,
            tool_calls=3,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.COST_UPDATE
        assert sse.data["input_tokens"] == 5000
        assert sse.data["total_cost_usd"] == 0.1275
        assert sse.data["tool_calls"] == 3

    def test_hypothesis_approval_requested(self) -> None:
        event = HypothesisApprovalRequested(
            hypotheses=[
                {"id": "h1", "statement": "Test hypothesis", "rationale": "Evidence"},
            ],
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.HYPOTHESIS_APPROVAL_REQUESTED
        assert len(sse.data["hypotheses"]) == 1
        assert sse.data["hypotheses"][0]["id"] == "h1"

    def test_unknown_event_returns_none(self) -> None:
        event = DomainEvent()
        sse = domain_event_to_sse(event)
        assert sse is None

    def test_sse_format_is_json(self) -> None:
        event = HypothesisFormulated(
            hypothesis_id="h1",
            statement="Test",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        formatted = sse.format()
        import json

        parsed = json.loads(formatted)
        assert parsed["event"] == "hypothesis_formulated"
        assert parsed["data"]["hypothesis_id"] == "h1"

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
    LiteratureSurveyCompleted,
    NegativeControlRecorded,
    PhaseChanged,
    PositiveControlRecorded,
    Thinking,
    ToolCalled,
    ToolResultEvent,
    ValidationMetricsComputed,
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

    def test_experiment_started_with_protocol(self) -> None:
        event = ExperimentStarted(
            experiment_id="e2",
            hypothesis_id="h1",
            description="Test DBO inhibition",
            independent_variable="C2 substituent pattern",
            dependent_variable="Ki (nM)",
            controls=["positive: Avibactam", "negative: Aspirin"],
            analysis_plan="AUC >0.7, docking <-7",
            success_criteria=">=3 candidates meet thresholds",
            failure_criteria="<2 compounds or AUC <0.7",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.EXPERIMENT_STARTED
        assert sse.data["independent_variable"] == "C2 substituent pattern"
        assert sse.data["dependent_variable"] == "Ki (nM)"
        assert len(sse.data["controls"]) == 2
        assert sse.data["analysis_plan"] == "AUC >0.7, docking <-7"
        assert sse.data["success_criteria"] == ">=3 candidates meet thresholds"
        assert sse.data["failure_criteria"] == "<2 compounds or AUC <0.7"

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

    def test_positive_control(self) -> None:
        event = PositiveControlRecorded(
            identifier="CC(=O)O",
            identifier_type="smiles",
            name="Avibactam",
            known_activity="Ki ~1 nM",
            score=0.92,
            correctly_classified=True,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.POSITIVE_CONTROL
        assert sse.data["name"] == "Avibactam"
        assert sse.data["known_activity"] == "Ki ~1 nM"
        assert sse.data["score"] == 0.92
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

    def test_validation_metrics_event(self) -> None:
        event = ValidationMetricsComputed(
            z_prime=0.72,
            z_prime_quality="excellent",
            positive_control_count=3,
            negative_control_count=4,
            positive_mean=0.85,
            negative_mean=0.12,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.VALIDATION_METRICS
        assert sse.data["z_prime"] == 0.72
        assert sse.data["z_prime_quality"] == "excellent"
        assert sse.data["positive_control_count"] == 3
        assert sse.data["negative_control_count"] == 4
        assert sse.data["positive_mean"] == 0.85
        assert sse.data["negative_mean"] == 0.12

    def test_completed_with_validation_metrics(self) -> None:
        event = InvestigationCompleted(
            investigation_id="inv-1",
            candidate_count=1,
            summary="Test",
            cost={},
            validation_metrics={"z_prime": 0.65, "z_prime_quality": "excellent"},
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.data["validation_metrics"]["z_prime"] == 0.65

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

    def test_finding_recorded_with_evidence_level(self) -> None:
        event = FindingRecorded(
            title="Meta-analysis result",
            detail="Pooled effect size 0.8",
            hypothesis_id="h1",
            evidence_type="supporting",
            evidence_level=1,
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.FINDING_RECORDED
        assert sse.data["evidence_level"] == 1

    def test_literature_survey_completed(self) -> None:
        event = LiteratureSurveyCompleted(
            pico={
                "population": "MRSA strains",
                "intervention": "beta-lactamase inhibitors",
                "comparison": "existing treatments",
                "outcome": "MIC reduction",
            },
            search_queries=5,
            total_results=47,
            included_results=12,
            evidence_grade="moderate",
            assessment="3 of 4 quality domains met",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.LITERATURE_SURVEY_COMPLETED
        assert sse.data["pico"]["population"] == "MRSA strains"
        assert sse.data["search_queries"] == 5
        assert sse.data["total_results"] == 47
        assert sse.data["included_results"] == 12
        assert sse.data["evidence_grade"] == "moderate"
        assert sse.data["assessment"] == "3 of 4 quality domains met"

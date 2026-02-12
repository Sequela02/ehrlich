from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.investigation.domain.events import HypothesisEvaluated
from ehrlich.investigation.domain.hypothesis import Hypothesis


class TestHypothesisCertaintyOfEvidence:
    def test_default_empty(self) -> None:
        h = Hypothesis(statement="Test claim", rationale="Reason")
        assert h.certainty_of_evidence == ""

    def test_accepts_high(self) -> None:
        h = Hypothesis(
            statement="Test claim",
            rationale="Reason",
            certainty_of_evidence="high",
        )
        assert h.certainty_of_evidence == "high"

    def test_accepts_moderate(self) -> None:
        h = Hypothesis(
            statement="Test claim",
            rationale="Reason",
            certainty_of_evidence="moderate",
        )
        assert h.certainty_of_evidence == "moderate"

    def test_accepts_low(self) -> None:
        h = Hypothesis(
            statement="Test claim",
            rationale="Reason",
            certainty_of_evidence="low",
        )
        assert h.certainty_of_evidence == "low"

    def test_accepts_very_low(self) -> None:
        h = Hypothesis(
            statement="Test claim",
            rationale="Reason",
            certainty_of_evidence="very_low",
        )
        assert h.certainty_of_evidence == "very_low"

    def test_mutable_after_creation(self) -> None:
        h = Hypothesis(statement="Test claim", rationale="Reason")
        h.certainty_of_evidence = "moderate"
        assert h.certainty_of_evidence == "moderate"

    def test_coexists_with_confidence(self) -> None:
        h = Hypothesis(
            statement="Test claim",
            rationale="Reason",
            confidence=0.85,
            certainty_of_evidence="high",
        )
        assert h.confidence == 0.85
        assert h.certainty_of_evidence == "high"


class TestHypothesisEvaluatedCertainty:
    def test_default_empty(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="supported",
            confidence=0.85,
            reasoning="Strong evidence",
            investigation_id="inv-1",
        )
        assert event.certainty_of_evidence == ""

    def test_carries_certainty(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="supported",
            confidence=0.85,
            reasoning="Strong evidence from tiers 1-3",
            certainty_of_evidence="high",
            investigation_id="inv-1",
        )
        assert event.certainty_of_evidence == "high"

    def test_carries_very_low(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h2",
            status="refuted",
            confidence=0.15,
            reasoning="Only qualitative reports",
            certainty_of_evidence="very_low",
            investigation_id="inv-1",
        )
        assert event.certainty_of_evidence == "very_low"


class TestSSECertaintyOfEvidence:
    def test_sse_includes_certainty(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="supported",
            confidence=0.85,
            reasoning="Strong evidence",
            certainty_of_evidence="moderate",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.event == SSEEventType.HYPOTHESIS_EVALUATED
        assert sse.data["certainty_of_evidence"] == "moderate"

    def test_sse_certainty_default_empty(self) -> None:
        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="refuted",
            confidence=0.2,
            reasoning="Weak evidence",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        assert sse.data["certainty_of_evidence"] == ""

    def test_sse_format_includes_certainty(self) -> None:
        import json

        event = HypothesisEvaluated(
            hypothesis_id="h1",
            status="supported",
            confidence=0.9,
            reasoning="Converging evidence",
            certainty_of_evidence="high",
            investigation_id="inv-1",
        )
        sse = domain_event_to_sse(event)
        assert sse is not None
        parsed = json.loads(sse.format())
        assert parsed["data"]["certainty_of_evidence"] == "high"

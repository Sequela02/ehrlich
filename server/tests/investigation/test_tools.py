import json

import pytest


class TestRecordFinding:
    @pytest.mark.asyncio
    async def test_returns_recorded_status(self) -> None:
        from ehrlich.investigation.tools import record_finding

        result = json.loads(await record_finding("Test finding", "Some detail"))
        assert result["status"] == "recorded"
        assert result["title"] == "Test finding"

    @pytest.mark.asyncio
    async def test_with_hypothesis_id(self) -> None:
        from ehrlich.investigation.tools import record_finding

        result = json.loads(
            await record_finding(
                "Finding", "Detail", hypothesis_id="h1", evidence_type="supporting"
            )
        )
        assert result["hypothesis_id"] == "h1"


class TestConcludeInvestigation:
    @pytest.mark.asyncio
    async def test_returns_concluded_status(self) -> None:
        from ehrlich.investigation.tools import conclude_investigation

        result = json.loads(await conclude_investigation("Summary of results"))
        assert result["status"] == "concluded"
        assert result["summary"] == "Summary of results"

    @pytest.mark.asyncio
    async def test_with_candidates_and_citations(self) -> None:
        from ehrlich.investigation.tools import conclude_investigation

        candidates = [{"smiles": "CCO", "name": "ethanol"}]
        citations = ["Doe et al. 2024"]
        result = json.loads(
            await conclude_investigation("Summary", candidates=candidates, citations=citations)
        )
        assert result["candidate_count"] == 1
        assert result["citation_count"] == 1

    @pytest.mark.asyncio
    async def test_without_optional_args(self) -> None:
        from ehrlich.investigation.tools import conclude_investigation

        result = json.loads(await conclude_investigation("Summary"))
        assert result["candidate_count"] == 0
        assert result["citation_count"] == 0


class TestProposeHypothesis:
    @pytest.mark.asyncio
    async def test_returns_proposed_status(self) -> None:
        from ehrlich.investigation.tools import propose_hypothesis

        result = json.loads(
            await propose_hypothesis("Compound X is active against MRSA", "Based on literature")
        )
        assert result["status"] == "proposed"
        assert result["statement"] == "Compound X is active against MRSA"


class TestDesignExperiment:
    @pytest.mark.asyncio
    async def test_returns_designed_status(self) -> None:
        from ehrlich.investigation.tools import design_experiment

        result = json.loads(
            await design_experiment("h1", "Test binding affinity", ["dock_against_target"])
        )
        assert result["status"] == "designed"
        assert result["hypothesis_id"] == "h1"
        assert result["tool_count"] == 1


class TestEvaluateHypothesis:
    @pytest.mark.asyncio
    async def test_returns_evaluated_status(self) -> None:
        from ehrlich.investigation.tools import evaluate_hypothesis

        result = json.loads(await evaluate_hypothesis("h1", "supported", 0.85, "Strong evidence"))
        assert result["status"] == "evaluated"
        assert result["hypothesis_id"] == "h1"
        assert result["confidence"] == 0.85


class TestRecordFindingWithEvidenceLevel:
    @pytest.mark.asyncio
    async def test_accepts_evidence_level(self) -> None:
        from ehrlich.investigation.tools import record_finding

        result = json.loads(
            await record_finding(
                "Meta-analysis result",
                "Pooled effect size 0.8",
                evidence_level=1,
            )
        )
        assert result["status"] == "recorded"

    @pytest.mark.asyncio
    async def test_default_evidence_level_zero(self) -> None:
        from ehrlich.investigation.tools import record_finding

        result = json.loads(await record_finding("Test", "Detail"))
        assert result["status"] == "recorded"


class TestRecordNegativeControl:
    @pytest.mark.asyncio
    async def test_returns_recorded_status(self) -> None:
        from ehrlich.investigation.tools import record_negative_control

        result = json.loads(
            await record_negative_control("CCO", "Ethanol", 0.1, source="Known inactive")
        )
        assert result["status"] == "recorded"
        assert result["correctly_classified"] is True

    @pytest.mark.asyncio
    async def test_high_score_is_misclassified(self) -> None:
        from ehrlich.investigation.tools import record_negative_control

        result = json.loads(await record_negative_control("CCO", "Ethanol", 0.8))
        assert result["correctly_classified"] is False

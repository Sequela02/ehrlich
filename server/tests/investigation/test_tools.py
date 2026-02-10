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
    async def test_with_phase(self) -> None:
        from ehrlich.investigation.tools import record_finding

        result = json.loads(await record_finding("Finding", "Detail", phase="Literature Review"))
        assert result["phase"] == "Literature Review"


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

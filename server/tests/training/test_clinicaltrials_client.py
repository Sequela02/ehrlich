from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.training.infrastructure.clinicaltrials_client import ClinicalTrialsClient


@pytest.fixture
def client() -> ClinicalTrialsClient:
    return ClinicalTrialsClient()


_BASE = "https://clinicaltrials.gov/api/v2/studies"

_STUDY_RESPONSE = {
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "HIIT vs MICT for VO2max in Runners",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2023-01-15"},
                },
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 120},
                },
                "conditionsModule": {
                    "conditions": ["Physical Fitness", "Exercise"],
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"name": "High Intensity Interval Training"},
                        {"name": "Moderate Intensity Continuous Training"},
                    ],
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {"measure": "Change in VO2max from baseline"},
                    ],
                },
            }
        }
    ]
}


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_trials(self, client: ClinicalTrialsClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_STUDY_RESPONSE))

        trials = await client.search("exercise", intervention="HIIT")
        assert len(trials) == 1
        t = trials[0]
        assert t.nct_id == "NCT12345678"
        assert t.title == "HIIT vs MICT for VO2max in Runners"
        assert t.status == "COMPLETED"
        assert t.phase == "PHASE3"
        assert t.enrollment == 120
        assert "Physical Fitness" in t.conditions
        assert "High Intensity Interval Training" in t.interventions
        assert "Change in VO2max from baseline" in t.primary_outcomes
        assert t.study_type == "INTERVENTIONAL"
        assert t.start_date == "2023-01-15"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: ClinicalTrialsClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"studies": []}))
        trials = await client.search("nonexistent condition")
        assert trials == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_intervention_param(self, client: ClinicalTrialsClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"studies": []}))
        await client.search("exercise")

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: ClinicalTrialsClient) -> None:
        respx.get(_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="ClinicalTrials.gov"):
            await client.search("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: ClinicalTrialsClient) -> None:
        route = respx.get(_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json={"studies": []}),
        ]
        trials = await client.search("retry test")
        assert trials == []


class TestParseStudy:
    def test_minimal_study(self) -> None:
        trial = ClinicalTrialsClient._parse_study({"protocolSection": {}})
        assert trial.nct_id == ""
        assert trial.enrollment == 0
        assert trial.conditions == ()

    def test_missing_protocol(self) -> None:
        trial = ClinicalTrialsClient._parse_study({})
        assert trial.nct_id == ""

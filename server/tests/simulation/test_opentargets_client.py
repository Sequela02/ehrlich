from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.infrastructure.opentargets_client import OpenTargetsClient

_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


@pytest.fixture
def client() -> OpenTargetsClient:
    return OpenTargetsClient()


def _disease_response(efo_id: str = "EFO_0000249", name: str = "Alzheimer disease") -> dict:
    return {"data": {"search": {"hits": [{"id": efo_id, "name": name}]}}}


def _targets_response(disease_name: str = "Alzheimer disease") -> dict:
    return {
        "data": {
            "disease": {
                "name": disease_name,
                "associatedTargets": {
                    "rows": [
                        {
                            "target": {
                                "id": "ENSG00000142192",
                                "approvedName": "amyloid beta precursor protein",
                                "tractability": {
                                    "smallmolecule": {"topCategory": "Clinical_Precedence"}
                                },
                                "knownDrugs": {"uniqueDrugs": 3},
                            },
                            "score": 0.85,
                            "datatypeScores": [
                                {"id": "genetic_association", "score": 0.9},
                                {"id": "known_drug", "score": 0.7},
                            ],
                        },
                        {
                            "target": {
                                "id": "ENSG00000186868",
                                "approvedName": "presenilin 1",
                                "tractability": {"smallmolecule": {}},
                                "knownDrugs": None,
                            },
                            "score": 0.72,
                            "datatypeScores": [{"id": "genetic_association", "score": 0.8}],
                        },
                    ]
                },
            }
        }
    }


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_associations(self, client: OpenTargetsClient) -> None:
        route = respx.post(_GRAPHQL_URL)
        route.side_effect = [
            Response(200, json=_disease_response()),
            Response(200, json=_targets_response()),
        ]

        results = await client.search("Alzheimer disease", limit=5)
        assert len(results) == 2
        assert results[0].target_id == "ENSG00000142192"
        assert results[0].target_name == "amyloid beta precursor protein"
        assert results[0].disease_name == "Alzheimer disease"
        assert results[0].association_score == 0.85
        assert results[0].evidence_count == 2
        assert results[0].tractability == "Clinical_Precedence"
        assert results[0].known_drugs == ["3 known drug(s)"]
        assert results[1].target_id == "ENSG00000186868"
        assert results[1].association_score == 0.72

    @respx.mock
    @pytest.mark.asyncio
    async def test_disease_not_found(self, client: OpenTargetsClient) -> None:
        respx.post(_GRAPHQL_URL).mock(
            return_value=Response(200, json={"data": {"search": {"hits": []}}})
        )
        results = await client.search("nonexistent disease")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_targets(self, client: OpenTargetsClient) -> None:
        route = respx.post(_GRAPHQL_URL)
        route.side_effect = [
            Response(200, json=_disease_response()),
            Response(
                200,
                json={
                    "data": {
                        "disease": {
                            "name": "Alzheimer disease",
                            "associatedTargets": {"rows": []},
                        }
                    }
                },
            ),
        ]
        results = await client.search("Alzheimer disease")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_raises(self, client: OpenTargetsClient) -> None:
        respx.post(_GRAPHQL_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="Open Targets"):
            await client.search("server error")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: OpenTargetsClient) -> None:
        route = respx.post(_GRAPHQL_URL)
        route.side_effect = [
            Response(429),
            Response(200, json={"data": {"search": {"hits": []}}}),
        ]
        results = await client.search("retry test")
        assert results == []

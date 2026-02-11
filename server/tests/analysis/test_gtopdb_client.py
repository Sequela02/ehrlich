from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.analysis.infrastructure.gtopdb_client import GtoPdbClient
from ehrlich.kernel.exceptions import ExternalServiceError

_BASE_URL = "https://www.guidetopharmacology.org/services"


@pytest.fixture
def client() -> GtoPdbClient:
    return GtoPdbClient()


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_entries(self, client: GtoPdbClient) -> None:
        respx.get(f"{_BASE_URL}/targets").mock(
            return_value=Response(
                200,
                json=[
                    {"targetId": 101, "name": "GABA-A receptor", "type": "LGIC"},
                ],
            )
        )
        respx.get(f"{_BASE_URL}/targets/101/interactions").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "ligand": {
                            "name": "Diazepam",
                            "smiles": "ClC1=CC2=C(C=C1)N(C)C(=O)CN=C2C3=CC=CC=C3",
                            "approved": True,
                        },
                        "affinityParameter": "pKi",
                        "affinity": "7.2",
                        "type": "Positive allosteric modulator",
                    },
                    {
                        "ligand": {
                            "name": "Flumazenil",
                            "smiles": "",
                            "approved": True,
                        },
                        "affinityParameter": "pKi",
                        "affinity": "8.1",
                        "type": "Antagonist",
                    },
                ],
            )
        )

        entries = await client.search("GABA-A receptor")
        assert len(entries) == 2
        assert entries[0].target_name == "GABA-A receptor"
        assert entries[0].target_family == "LGIC"
        assert entries[0].ligand_name == "Diazepam"
        assert entries[0].affinity_type == "pKi"
        assert entries[0].affinity_value == 7.2
        assert entries[0].action == "Positive allosteric modulator"
        assert entries[0].approved is True
        assert entries[1].ligand_name == "Flumazenil"
        assert entries[1].affinity_value == 8.1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_targets(self, client: GtoPdbClient) -> None:
        respx.get(f"{_BASE_URL}/targets").mock(return_value=Response(200, json=[]))
        entries = await client.search("nonexistent target")
        assert entries == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_raises(self, client: GtoPdbClient) -> None:
        respx.get(f"{_BASE_URL}/targets").mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="GtoPdb"):
            await client.search("server error")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_with_family_filter(self, client: GtoPdbClient) -> None:
        route = respx.get(f"{_BASE_URL}/targets").mock(return_value=Response(200, json=[]))
        await client.search("receptor", family="GPCR")
        request = route.calls[0].request
        assert "type" in str(request.url.params)
        assert request.url.params.get("type") == "GPCR"

    @respx.mock
    @pytest.mark.asyncio
    async def test_limits_to_three_targets(self, client: GtoPdbClient) -> None:
        respx.get(f"{_BASE_URL}/targets").mock(
            return_value=Response(
                200,
                json=[{"targetId": i, "name": f"Target {i}", "type": "GPCR"} for i in range(5)],
            )
        )
        for i in range(5):
            respx.get(f"{_BASE_URL}/targets/{i}/interactions").mock(
                return_value=Response(200, json=[])
            )
        await client.search("receptor")
        # Only first 3 targets should have interaction requests
        interaction_calls = [c for c in respx.calls if "/interactions" in str(c.request.url)]
        assert len(interaction_calls) == 3


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: GtoPdbClient) -> None:
        route = respx.get(f"{_BASE_URL}/targets")
        route.side_effect = [
            Response(429),
            Response(200, json=[]),
        ]
        entries = await client.search("retry test")
        assert entries == []

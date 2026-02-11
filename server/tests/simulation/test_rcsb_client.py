from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.infrastructure.rcsb_client import RCSBClient


@pytest.fixture
def client() -> RCSBClient:
    return RCSBClient()


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_targets(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(
            return_value=Response(
                200,
                json={
                    "result_set": [
                        {"identifier": "1VQQ"},
                        {"identifier": "2XCT"},
                    ]
                },
            )
        )
        respx.get("https://data.rcsb.org/rest/v1/core/entry/1VQQ").mock(
            return_value=Response(
                200,
                json={
                    "struct": {"title": "PBP2a"},
                    "rcsb_entry_container_identifiers": {"entry_id": "1VQQ"},
                    "polymer_entities": [
                        {
                            "rcsb_entity_source_organism": [
                                {"ncbi_scientific_name": "Staphylococcus aureus"}
                            ]
                        }
                    ],
                },
            )
        )
        respx.get("https://data.rcsb.org/rest/v1/core/entry/2XCT").mock(
            return_value=Response(
                200,
                json={
                    "struct": {"title": "DNA Gyrase"},
                    "rcsb_entry_container_identifiers": {"entry_id": "2XCT"},
                },
            )
        )

        targets = await client.search("beta-lactam resistance", organism="Staphylococcus")
        assert len(targets) == 2
        assert targets[0].pdb_id == "1VQQ"
        assert targets[0].name == "PBP2a"
        assert targets[0].organism == "Staphylococcus aureus"
        assert targets[0].box_size == 22.0
        assert targets[1].pdb_id == "2XCT"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(
            return_value=Response(200, json={"result_set": []})
        )
        targets = await client.search("nonexistent protein")
        assert targets == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_entry_404_skipped(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(
            return_value=Response(200, json={"result_set": [{"identifier": "XXXX"}]})
        )
        respx.get("https://data.rcsb.org/rest/v1/core/entry/XXXX").mock(return_value=Response(404))
        targets = await client.search("deleted entry")
        assert targets == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_raises(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="RCSB PDB"):
            await client.search("server error")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_without_organism(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(
            return_value=Response(200, json={"result_set": []})
        )
        targets = await client.search("kinase")
        assert targets == []


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: RCSBClient) -> None:
        route = respx.post("https://search.rcsb.org/rcsbsearch/v2/query")
        route.side_effect = [
            Response(429),
            Response(200, json={"result_set": []}),
        ]
        targets = await client.search("retry test")
        assert targets == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_entry_http_error_skipped(self, client: RCSBClient) -> None:
        respx.post("https://search.rcsb.org/rcsbsearch/v2/query").mock(
            return_value=Response(200, json={"result_set": [{"identifier": "ERR1"}]})
        )
        respx.get("https://data.rcsb.org/rest/v1/core/entry/ERR1").mock(return_value=Response(500))
        targets = await client.search("error entry")
        assert targets == []


class TestBuildQuery:
    def test_with_organism(self, client: RCSBClient) -> None:
        query = client._build_query("PBP2a", "Staphylococcus", 5)
        assert query["query"]["type"] == "group"
        assert query["query"]["logical_operator"] == "and"
        assert len(query["query"]["nodes"]) == 2

    def test_without_organism(self, client: RCSBClient) -> None:
        query = client._build_query("kinase", "", 10)
        assert query["query"]["type"] == "terminal"
        assert query["query"]["service"] == "full_text"

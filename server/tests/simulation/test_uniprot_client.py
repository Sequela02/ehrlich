from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.infrastructure.uniprot_client import UniProtClient


@pytest.fixture
def client() -> UniProtClient:
    return UniProtClient()


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_annotations(self, client: UniProtClient) -> None:
        respx.get("https://rest.uniprot.org/uniprotkb/search").mock(
            return_value=Response(
                200,
                json={
                    "results": [
                        {
                            "primaryAccession": "P0A0K9",
                            "proteinDescription": {
                                "recommendedName": {"fullName": {"value": "PBP2a"}}
                            },
                            "organism": {"scientificName": "Staphylococcus aureus"},
                            "comments": [
                                {
                                    "commentType": "FUNCTION",
                                    "texts": [
                                        {"value": "Penicillin-binding protein with low affinity"}
                                    ],
                                },
                                {
                                    "commentType": "DISEASE",
                                    "disease": {"diseaseId": "Methicillin resistance"},
                                },
                            ],
                            "uniProtKBCrossReferences": [
                                {
                                    "database": "GO",
                                    "id": "GO:0008658",
                                    "properties": [
                                        {
                                            "key": "GoTerm",
                                            "value": "P:peptidoglycan biosynthesis",
                                        }
                                    ],
                                },
                                {"database": "PDB", "id": "1VQQ"},
                                {
                                    "database": "Reactome",
                                    "id": "R-SSA-123",
                                    "properties": [
                                        {
                                            "key": "PathwayName",
                                            "value": "Cell wall synthesis",
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "primaryAccession": "Q9X5V8",
                            "proteinDescription": {
                                "recommendedName": {"fullName": {"value": "Beta-lactamase"}}
                            },
                            "organism": {"scientificName": "Escherichia coli"},
                            "comments": [],
                            "uniProtKBCrossReferences": [],
                        },
                    ]
                },
            )
        )

        annotations = await client.search("penicillin-binding protein")
        assert len(annotations) == 2
        assert annotations[0].accession == "P0A0K9"
        assert annotations[0].name == "PBP2a"
        assert annotations[0].organism == "Staphylococcus aureus"
        assert "low affinity" in annotations[0].function
        assert annotations[0].disease_associations == ["Methicillin resistance"]
        assert annotations[0].go_terms == ["P:peptidoglycan biosynthesis"]
        assert annotations[0].pdb_cross_refs == ["1VQQ"]
        assert annotations[0].pathway == "Cell wall synthesis"
        assert annotations[1].accession == "Q9X5V8"
        assert annotations[1].name == "Beta-lactamase"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: UniProtClient) -> None:
        respx.get("https://rest.uniprot.org/uniprotkb/search").mock(
            return_value=Response(200, json={"results": []})
        )
        annotations = await client.search("nonexistent protein")
        assert annotations == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_raises(self, client: UniProtClient) -> None:
        respx.get("https://rest.uniprot.org/uniprotkb/search").mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="UniProt"):
            await client.search("server error")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_with_organism_filter(self, client: UniProtClient) -> None:
        route = respx.get("https://rest.uniprot.org/uniprotkb/search").mock(
            return_value=Response(200, json={"results": []})
        )
        await client.search("kinase", organism="Homo sapiens")
        request = route.calls[0].request
        query_param = str(request.url.params.get("query", ""))
        assert "organism_name:Homo sapiens" in query_param


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: UniProtClient) -> None:
        route = respx.get("https://rest.uniprot.org/uniprotkb/search")
        route.side_effect = [
            Response(429),
            Response(200, json={"results": []}),
        ]
        annotations = await client.search("retry test")
        assert annotations == []

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.analysis.infrastructure.pubchem_client import PubChemClient
from ehrlich.kernel.exceptions import ExternalServiceError


@pytest.fixture
def client() -> PubChemClient:
    return PubChemClient()


def _compound_json(cid: int = 2244, smiles: str = "CC(=O)Oc1ccccc1C(=O)O") -> dict:
    return {
        "PC_Compounds": [
            {
                "id": {"id": {"cid": cid}},
                "props": [
                    {
                        "urn": {"label": "SMILES", "name": "Canonical"},
                        "value": {"sval": smiles},
                    },
                    {
                        "urn": {"label": "IUPAC Name", "name": "Preferred"},
                        "value": {"sval": "aspirin"},
                    },
                    {
                        "urn": {"label": "Molecular Formula"},
                        "value": {"sval": "C9H8O4"},
                    },
                    {
                        "urn": {"label": "Molecular Weight"},
                        "value": {"sval": "180.16"},
                    },
                ],
            }
        ]
    }


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_search_by_name(self, client: PubChemClient) -> None:
        respx.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/JSON").mock(
            return_value=Response(200, json=_compound_json())
        )
        results = await client.search("aspirin")
        assert len(results) == 1
        assert results[0].cid == 2244
        assert results[0].smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert results[0].iupac_name == "aspirin"
        assert results[0].molecular_formula == "C9H8O4"
        assert results[0].molecular_weight == 180.16
        assert results[0].source == "pubchem"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_not_found(self, client: PubChemClient) -> None:
        respx.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/zzzzz/JSON").mock(
            return_value=Response(404)
        )
        results = await client.search("zzzzz")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: PubChemClient) -> None:
        respx.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/bad/JSON").mock(
            return_value=Response(500)
        )
        with pytest.raises(ExternalServiceError, match="PubChem"):
            await client.search("bad")


class TestSearchBySimilarity:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_similar(self, client: PubChemClient) -> None:
        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity_2d/"
            "smiles/CC%28%3DO%29Oc1ccccc1C%28%3DO%29O/JSON"
        )
        respx.get(url).mock(return_value=Response(200, json=_compound_json()))
        results = await client.search_by_similarity("CC(=O)Oc1ccccc1C(=O)O", threshold=0.8)
        assert len(results) == 1
        assert results[0].cid == 2244


class TestParseCompounds:
    def test_empty_data(self) -> None:
        assert PubChemClient._parse_compounds({}, 10) == []

    def test_no_smiles_skipped(self) -> None:
        data = {
            "PC_Compounds": [
                {
                    "id": {"id": {"cid": 123}},
                    "props": [
                        {
                            "urn": {"label": "IUPAC Name", "name": "Preferred"},
                            "value": {"sval": "test"},
                        },
                    ],
                }
            ]
        }
        assert PubChemClient._parse_compounds(data, 10) == []

    def test_limit_respected(self) -> None:
        compounds = [
            {
                "id": {"id": {"cid": i}},
                "props": [
                    {
                        "urn": {"label": "SMILES", "name": "Canonical"},
                        "value": {"sval": f"C{'C' * i}"},
                    },
                ],
            }
            for i in range(1, 6)
        ]
        results = PubChemClient._parse_compounds({"PC_Compounds": compounds}, 2)
        assert len(results) == 2

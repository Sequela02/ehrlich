from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.nutrition.infrastructure.rxnav_client import RxNavClient


@pytest.fixture
def client() -> RxNavClient:
    return RxNavClient()


_RXCUI_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
_INTERACTION_URL = "https://rxnav.nlm.nih.gov/REST/interaction/interaction.json"

_RXCUI_RESPONSE = {"idGroup": {"rxnormId": ["7052"]}}

_INTERACTION_RESPONSE = {
    "interactionTypeGroup": [
        {
            "interactionType": [
                {
                    "interactionPair": [
                        {
                            "interactionConcept": [
                                {
                                    "sourceConceptItem": {
                                        "name": "aspirin",
                                    }
                                },
                                {
                                    "sourceConceptItem": {
                                        "name": "warfarin",
                                    }
                                },
                            ],
                            "description": "Increased risk of bleeding",
                            "severity": "high",
                        }
                    ]
                }
            ]
        }
    ]
}


class TestSearchInteractions:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_interactions(self, client: RxNavClient) -> None:
        respx.get(_RXCUI_URL).mock(return_value=Response(200, json=_RXCUI_RESPONSE))
        respx.get(_INTERACTION_URL).mock(return_value=Response(200, json=_INTERACTION_RESPONSE))

        results = await client.search_interactions("aspirin")
        assert len(results) == 1
        ix = results[0]
        assert ix.drug_a == "aspirin"
        assert ix.drug_b == "warfarin"
        assert ix.severity == "high"
        assert ix.description == "Increased risk of bleeding"
        assert ix.source == "RxNav"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_rxcui(self, client: RxNavClient) -> None:
        respx.get(_RXCUI_URL).mock(return_value=Response(200, json={"idGroup": {}}))
        results = await client.search_interactions("nonexistent")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_interactions(self, client: RxNavClient) -> None:
        respx.get(_RXCUI_URL).mock(return_value=Response(200, json=_RXCUI_RESPONSE))
        respx.get(_INTERACTION_URL).mock(
            return_value=Response(200, json={"interactionTypeGroup": []})
        )
        results = await client.search_interactions("aspirin")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: RxNavClient) -> None:
        respx.get(_RXCUI_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="RxNav"):
            await client.search_interactions("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: RxNavClient) -> None:
        rxcui_route = respx.get(_RXCUI_URL)
        rxcui_route.side_effect = [
            Response(429),
            Response(200, json=_RXCUI_RESPONSE),
        ]
        respx.get(_INTERACTION_URL).mock(
            return_value=Response(200, json={"interactionTypeGroup": []})
        )
        results = await client.search_interactions("retry test")
        assert results == []


class TestParsePair:
    def test_missing_concepts(self) -> None:
        result = RxNavClient._parse_pair({"interactionConcept": []}, "aspirin")
        assert result is None

    def test_missing_name(self) -> None:
        result = RxNavClient._parse_pair(
            {
                "interactionConcept": [
                    {"sourceConceptItem": {"name": "aspirin"}},
                    {"sourceConceptItem": {}},
                ]
            },
            "aspirin",
        )
        assert result is None

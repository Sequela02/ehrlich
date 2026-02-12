from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.sports.infrastructure.openfda_client import OpenFDAClient


@pytest.fixture
def client() -> OpenFDAClient:
    return OpenFDAClient()


_BASE = "https://api.fda.gov/food/event.json"

_FDA_RESPONSE = {
    "results": [
        {
            "report_number": "FDA-2023-001",
            "date_started": "20230315",
            "products": [
                {"name_brand": "Super Pre-Workout X"},
            ],
            "reactions": [
                {"reaction": "NAUSEA"},
                {"reaction": "TACHYCARDIA"},
            ],
            "outcomes": ["Hospitalization"],
            "consumer": {
                "age": "28",
                "gender": "Male",
            },
        }
    ]
}


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_events(self, client: OpenFDAClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_FDA_RESPONSE))

        events = await client.search("pre-workout")
        assert len(events) == 1
        e = events[0]
        assert e.report_id == "FDA-2023-001"
        assert e.date == "20230315"
        assert "Super Pre-Workout X" in e.products
        assert "NAUSEA" in e.reactions
        assert "TACHYCARDIA" in e.reactions
        assert "Hospitalization" in e.outcomes
        assert e.consumer_age == "28"
        assert e.consumer_gender == "Male"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: OpenFDAClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"results": []}))
        events = await client.search("nonexistent")
        assert events == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_returns_empty(self, client: OpenFDAClient) -> None:
        respx.get(_BASE).mock(return_value=Response(404))
        events = await client.search("nothing here")
        assert events == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: OpenFDAClient) -> None:
        respx.get(_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="OpenFDA"):
            await client.search("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: OpenFDAClient) -> None:
        route = respx.get(_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json={"results": []}),
        ]
        events = await client.search("retry test")
        assert events == []


class TestParseEvent:
    def test_missing_fields(self) -> None:
        event = OpenFDAClient._parse_event({})
        assert event.report_id == ""
        assert event.products == ()
        assert event.reactions == ()

    def test_missing_consumer(self) -> None:
        event = OpenFDAClient._parse_event({"report_number": "X"})
        assert event.consumer_age == ""
        assert event.consumer_gender == ""

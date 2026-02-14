"""Tests for WHO GHO API client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.impact.infrastructure.who_client import WHOClient
from ehrlich.kernel.exceptions import ExternalServiceError


@pytest.fixture
def client() -> WHOClient:
    return WHOClient()


_BASE = "https://ghoapi.azureedge.net/api/WHOSIS_000001"

_WHO_RESPONSE = {
    "value": [
        {
            "IndicatorCode": "WHOSIS_000001",
            "SpatialDim": "MEX",
            "TimeDim": 2020,
            "NumericValue": 75.1,
            "Dim1": "Both sexes",
        },
        {
            "IndicatorCode": "WHOSIS_000001",
            "SpatialDim": "MEX",
            "TimeDim": 2019,
            "NumericValue": 74.8,
            "Dim1": "Both sexes",
        },
    ]
}


class TestSearchIndicators:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_indicators(self, client: WHOClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_WHO_RESPONSE))
        results = await client.search_indicators("WHOSIS_000001")
        assert len(results) == 2
        assert results[0].indicator_code == "WHOSIS_000001"
        assert results[0].value == 75.1
        assert results[0].country == "MEX"
        assert results[0].year == 2020

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_country_filter(self, client: WHOClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_WHO_RESPONSE))
        results = await client.search_indicators("WHOSIS_000001", country="MEX")
        assert len(results) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_year_range(self, client: WHOClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_WHO_RESPONSE))
        results = await client.search_indicators("WHOSIS_000001", year_start=2019, year_end=2020)
        assert len(results) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: WHOClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"value": []}))
        results = await client.search_indicators("WHOSIS_000001")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_null_numeric_value_skipped(self, client: WHOClient) -> None:
        data = {
            "value": [
                {"IndicatorCode": "X", "SpatialDim": "MEX", "TimeDim": 2020, "NumericValue": None}
            ]
        }
        respx.get(_BASE).mock(return_value=Response(200, json=data))
        results = await client.search_indicators("WHOSIS_000001")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: WHOClient) -> None:
        respx.get(_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="WHO GHO"):
            await client.search_indicators("WHOSIS_000001")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: WHOClient) -> None:
        route = respx.get(_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json={"value": []}),
        ]
        results = await client.search_indicators("WHOSIS_000001")
        assert results == []

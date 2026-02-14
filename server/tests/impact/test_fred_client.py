"""Tests for FRED API client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.impact.infrastructure.fred_client import FREDClient
from ehrlich.kernel.exceptions import ExternalServiceError


@pytest.fixture
def client() -> FREDClient:
    return FREDClient(api_key="test_key")


_SEARCH_URL = "https://api.stlouisfed.org/fred/series/search"
_OBS_URL = "https://api.stlouisfed.org/fred/series/observations"

_SEARCH_RESPONSE = {
    "seriess": [
        {
            "id": "GDP",
            "title": "Gross Domestic Product",
            "units": "Billions of Dollars",
            "frequency": "Quarterly",
        },
        {
            "id": "GDPC1",
            "title": "Real Gross Domestic Product",
            "units": "Billions of Chained 2017 Dollars",
            "frequency": "Quarterly",
        },
    ]
}

_OBS_RESPONSE = {
    "observations": [
        {"date": "2020-01-01", "value": "21481.367"},
        {"date": "2020-04-01", "value": "19520.164"},
        {"date": "2020-07-01", "value": "."},
        {"date": "2020-10-01", "value": "21477.597"},
    ]
}


class TestSearchSeries:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_series(self, client: FREDClient) -> None:
        respx.get(_SEARCH_URL).mock(return_value=Response(200, json=_SEARCH_RESPONSE))
        results = await client.search_series("GDP")
        assert len(results) == 2
        assert results[0].series_id == "GDP"
        assert results[0].title == "Gross Domestic Product"
        assert results[0].unit == "Billions of Dollars"
        assert results[0].source == "fred"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: FREDClient) -> None:
        respx.get(_SEARCH_URL).mock(return_value=Response(200, json={"seriess": []}))
        results = await client.search_series("nonexistent")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: FREDClient) -> None:
        respx.get(_SEARCH_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="FRED"):
            await client.search_series("GDP")

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self) -> None:
        client = FREDClient(api_key="")
        results = await client.search_series("GDP")
        assert results == []


class TestGetSeries:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_observations(self, client: FREDClient) -> None:
        respx.get(_OBS_URL).mock(return_value=Response(200, json=_OBS_RESPONSE))
        result = await client.get_series("GDP")
        assert result is not None
        assert result.series_id == "GDP"
        assert len(result.values) == 3  # "." values are skipped
        assert result.values[0].date == "2020-01-01"
        assert result.values[0].value == 21481.367

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_date_range(self, client: FREDClient) -> None:
        respx.get(_OBS_URL).mock(return_value=Response(200, json=_OBS_RESPONSE))
        result = await client.get_series("GDP", start="2020-01-01", end="2020-12-31")
        assert result is not None

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_observations(self, client: FREDClient) -> None:
        respx.get(_OBS_URL).mock(return_value=Response(200, json={"observations": []}))
        result = await client.get_series("EMPTY")
        assert result is not None
        assert result.values == ()

    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self) -> None:
        client = FREDClient(api_key="")
        result = await client.get_series("GDP")
        assert result is None


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: FREDClient) -> None:
        route = respx.get(_SEARCH_URL)
        route.side_effect = [
            Response(429),
            Response(200, json={"seriess": []}),
        ]
        results = await client.search_series("GDP")
        assert results == []

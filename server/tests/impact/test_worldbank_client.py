"""Tests for World Bank API client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.impact.infrastructure.worldbank_client import WorldBankClient
from ehrlich.kernel.exceptions import ExternalServiceError


@pytest.fixture
def client() -> WorldBankClient:
    return WorldBankClient()


_INDICATOR_URL = "https://api.worldbank.org/v2/country/MX/indicator/SE.PRM.ENRR"
_ALL_INDICATOR_URL = "https://api.worldbank.org/v2/country/all/indicator/SE.PRM.ENRR"
_COUNTRIES_URL = "https://api.worldbank.org/v2/country"

_INDICATOR_RESPONSE = [
    {"page": 1, "pages": 1, "per_page": 10, "total": 1},
    [
        {
            "indicator": {"id": "SE.PRM.ENRR", "value": "School enrollment, primary (% net)"},
            "country": {"id": "MX", "value": "Mexico"},
            "value": 98.5,
            "unit": "",
            "date": "2020",
        },
        {
            "indicator": {"id": "SE.PRM.ENRR", "value": "School enrollment, primary (% net)"},
            "country": {"id": "MX", "value": "Mexico"},
            "value": 97.2,
            "unit": "",
            "date": "2019",
        },
    ],
]

_COUNTRIES_RESPONSE = [
    {"page": 1, "pages": 1, "per_page": 300, "total": 2},
    [
        {
            "id": "MEX",
            "name": "Mexico",
            "iso2Code": "MX",
            "region": {"value": "Latin America & Caribbean"},
            "incomeLevel": {"value": "Upper middle income"},
        },
        {
            "id": "USA",
            "name": "United States",
            "iso2Code": "US",
            "region": {"value": "North America"},
            "incomeLevel": {"value": "High income"},
        },
    ],
]


class TestSearchIndicators:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_benchmarks(self, client: WorldBankClient) -> None:
        respx.get(_INDICATOR_URL).mock(return_value=Response(200, json=_INDICATOR_RESPONSE))
        results = await client.search_indicators("SE.PRM.ENRR", country="MX")
        assert len(results) == 2
        assert results[0].source == "world_bank"
        assert results[0].value == 98.5
        assert results[0].geography == "Mexico"
        assert results[0].period == "2020"

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_country_uses_all(self, client: WorldBankClient) -> None:
        respx.get(_ALL_INDICATOR_URL).mock(return_value=Response(200, json=_INDICATOR_RESPONSE))
        results = await client.search_indicators("SE.PRM.ENRR")
        assert len(results) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_data(self, client: WorldBankClient) -> None:
        respx.get(_ALL_INDICATOR_URL).mock(return_value=Response(200, json=[{"page": 1}, None]))
        results = await client.search_indicators("SE.PRM.ENRR")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_null_values_skipped(self, client: WorldBankClient) -> None:
        data = [
            {"page": 1},
            [
                {
                    "indicator": {"value": "test"},
                    "country": {"value": "Mexico"},
                    "value": None,
                    "date": "2020",
                    "unit": "",
                },
            ],
        ]
        respx.get(_ALL_INDICATOR_URL).mock(return_value=Response(200, json=data))
        results = await client.search_indicators("SE.PRM.ENRR")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: WorldBankClient) -> None:
        respx.get(_ALL_INDICATOR_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="World Bank"):
            await client.search_indicators("SE.PRM.ENRR")


class TestGetCountries:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_countries(self, client: WorldBankClient) -> None:
        respx.get(_COUNTRIES_URL).mock(return_value=Response(200, json=_COUNTRIES_RESPONSE))
        countries = await client.get_countries()
        assert len(countries) == 2
        assert countries[0]["id"] == "MEX"
        assert countries[0]["name"] == "Mexico"
        assert countries[1]["id"] == "USA"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_response(self, client: WorldBankClient) -> None:
        respx.get(_COUNTRIES_URL).mock(return_value=Response(200, json=[{"page": 1}]))
        countries = await client.get_countries()
        assert countries == []


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: WorldBankClient) -> None:
        route = respx.get(_ALL_INDICATOR_URL)
        route.side_effect = [
            Response(429),
            Response(200, json=[{"page": 1}, []]),
        ]
        results = await client.search_indicators("SE.PRM.ENRR")
        assert results == []

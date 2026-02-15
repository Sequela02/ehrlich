"""Tests for US federal data API clients."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.impact.infrastructure.bls_client import BLSClient
from ehrlich.impact.infrastructure.cdc_client import CDCWonderClient
from ehrlich.impact.infrastructure.census_client import CensusClient
from ehrlich.impact.infrastructure.college_scorecard_client import CollegeScorecardClient
from ehrlich.impact.infrastructure.datagov_client import DataGovClient
from ehrlich.impact.infrastructure.hud_client import HUDClient
from ehrlich.impact.infrastructure.usaspending_client import USAspendingClient
from ehrlich.kernel.exceptions import ExternalServiceError

# --- Census ---

_CENSUS_URL = "https://api.census.gov/data/2022/acs/acs5"
_CENSUS_RESPONSE = [
    ["NAME", "B19013_001E", "state"],
    ["California", "78672", "06"],
    ["Texas", "63826", "48"],
]


class TestCensusClient:
    @pytest.fixture
    def client(self) -> CensusClient:
        return CensusClient(api_key="test_key")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_indicators(self, client: CensusClient) -> None:
        respx.get(_CENSUS_URL).mock(return_value=Response(200, json=_CENSUS_RESPONSE))
        results = await client.search_indicators("median_income")
        assert len(results) == 2
        assert results[0].source == "census"
        assert results[0].geography == "California"
        assert results[0].value == 78672.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_response(self, client: CensusClient) -> None:
        respx.get(_CENSUS_URL).mock(return_value=Response(200, json=[["NAME", "X"]]))
        results = await client.search_indicators("population")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: CensusClient) -> None:
        respx.get(_CENSUS_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="Census"):
            await client.search_indicators("median_income")

    @pytest.mark.asyncio
    async def test_get_countries_returns_empty(self) -> None:
        client = CensusClient(api_key="test")
        result = await client.get_countries()
        assert result == []


# --- BLS ---

_BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
_BLS_RESPONSE = {
    "status": "REQUEST_SUCCEEDED",
    "Results": {
        "series": [
            {
                "seriesID": "LNS14000000",
                "data": [
                    {"year": "2023", "period": "M12", "value": "3.7"},
                    {"year": "2023", "period": "M11", "value": "3.7"},
                ],
            }
        ]
    },
}


class TestBLSClient:
    @pytest.fixture
    def client(self) -> BLSClient:
        return BLSClient(api_key="test_key")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_series(self, client: BLSClient) -> None:
        respx.post(_BLS_URL).mock(return_value=Response(200, json=_BLS_RESPONSE))
        results = await client.search_series("LNS14000000")
        assert len(results) == 1
        assert results[0].series_id == "LNS14000000"
        assert results[0].source == "bls"
        assert len(results[0].values) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_series(self, client: BLSClient) -> None:
        respx.post(_BLS_URL).mock(return_value=Response(200, json=_BLS_RESPONSE))
        result = await client.get_series("LNS14000000", start="2023", end="2023")
        assert result is not None
        assert result.series_id == "LNS14000000"

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self) -> None:
        client = BLSClient(api_key="")
        results = await client.search_series("LNS14000000")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: BLSClient) -> None:
        respx.post(_BLS_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="BLS"):
            await client.search_series("LNS14000000")

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: BLSClient) -> None:
        respx.post(_BLS_URL).mock(return_value=Response(200, json={"Results": {"series": []}}))
        results = await client.search_series("UNKNOWN")
        assert results == []


# --- USAspending ---

_USASPENDING_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
_USASPENDING_RESPONSE = {
    "results": [
        {
            "Award ID": "AWARD-001",
            "Recipient Name": "Test University",
            "Award Amount": 500000.0,
            "Awarding Agency": "Department of Education",
            "Award Type": "Grant",
            "Start Date": "2023-01-01",
            "internal_id": "1",
        }
    ]
}


class TestUSAspendingClient:
    @pytest.fixture
    def client(self) -> USAspendingClient:
        return USAspendingClient()

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_awards(self, client: USAspendingClient) -> None:
        respx.post(_USASPENDING_URL).mock(return_value=Response(200, json=_USASPENDING_RESPONSE))
        results = await client.search_awards("education")
        assert len(results) == 1
        assert results[0].award_id == "AWARD-001"
        assert results[0].recipient_name == "Test University"
        assert results[0].amount == 500000.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: USAspendingClient) -> None:
        respx.post(_USASPENDING_URL).mock(return_value=Response(200, json={"results": []}))
        results = await client.search_awards("nonexistent")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_filters(self, client: USAspendingClient) -> None:
        respx.post(_USASPENDING_URL).mock(return_value=Response(200, json=_USASPENDING_RESPONSE))
        results = await client.search_awards("Head Start", agency="HHS", year=2023)
        assert len(results) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: USAspendingClient) -> None:
        respx.post(_USASPENDING_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="USAspending"):
            await client.search_awards("test")


# --- College Scorecard ---

_SCORECARD_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
_SCORECARD_RESPONSE = {
    "results": [
        {
            "id": "12345",
            "school": {"name": "Test University", "state": "CA"},
            "latest": {
                "student": {"size": 5000},
                "cost": {"avg_net_price": {"overall": 15000}},
                "completion": {"rate_suppressed": {"overall": 0.65}},
                "earnings": {"10_yrs_after_entry": {"median": 55000}},
            },
        }
    ]
}


class TestCollegeScorecardClient:
    @pytest.fixture
    def client(self) -> CollegeScorecardClient:
        return CollegeScorecardClient(api_key="test_key")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_schools(self, client: CollegeScorecardClient) -> None:
        respx.get(_SCORECARD_URL).mock(return_value=Response(200, json=_SCORECARD_RESPONSE))
        results = await client.search_schools("Test University")
        assert len(results) == 1
        assert results[0].name == "Test University"
        assert results[0].state == "CA"
        assert results[0].student_size == 5000
        assert results[0].completion_rate == 0.65
        assert results[0].earnings_median == 55000.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: CollegeScorecardClient) -> None:
        respx.get(_SCORECARD_URL).mock(return_value=Response(200, json={"results": []}))
        results = await client.search_schools("nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self) -> None:
        client = CollegeScorecardClient(api_key="")
        results = await client.search_schools("test")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: CollegeScorecardClient) -> None:
        respx.get(_SCORECARD_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="College Scorecard"):
            await client.search_schools("test")


# --- HUD ---

_HUD_URL = "https://www.huduser.gov/hudapi/public/fmr/statedata/CA"
_HUD_RESPONSE = {
    "data": {
        "area_name": "Los Angeles",
        "fmr_0": 1200,
        "fmr_1": 1500,
        "fmr_2": 1900,
        "fmr_3": 2400,
        "fmr_4": 2800,
        "median_income": 75000,
    }
}


class TestHUDClient:
    @pytest.fixture
    def client(self) -> HUDClient:
        return HUDClient(api_token="test_token")

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_housing_data(self, client: HUDClient) -> None:
        respx.get(_HUD_URL).mock(return_value=Response(200, json=_HUD_RESPONSE))
        results = await client.search_housing_data("CA")
        assert len(results) == 1
        assert results[0].area_name == "Los Angeles"
        assert results[0].state == "CA"
        assert results[0].fmr_2br == 1900.0
        assert results[0].median_income == 75000.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_response(self, client: HUDClient) -> None:
        respx.get(_HUD_URL).mock(return_value=Response(200, json={"data": [_HUD_RESPONSE["data"]]}))
        results = await client.search_housing_data("CA")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_no_token_returns_empty(self) -> None:
        client = HUDClient(api_token="")
        results = await client.search_housing_data("CA")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: HUDClient) -> None:
        respx.get(_HUD_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="HUD"):
            await client.search_housing_data("CA")


# --- CDC WONDER ---

_CDC_URL = "https://wonder.cdc.gov/controller/datarequest/D76"
_CDC_XML_RESPONSE = """<?xml version="1.0" encoding="utf-8"?>
<page>
<response>
<data-table>
<r><c v="2020" l="2020"/><c v="3383729"/><c v="828.7"/></r>
<r><c v="2021" l="2021"/><c v="3458697"/><c v="879.7"/></r>
</data-table>
</response>
</page>
"""


class TestCDCWonderClient:
    @pytest.fixture
    def client(self) -> CDCWonderClient:
        return CDCWonderClient()

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_indicators(self, client: CDCWonderClient) -> None:
        respx.post(_CDC_URL).mock(return_value=Response(200, text=_CDC_XML_RESPONSE))
        results = await client.search_indicators("mortality")
        assert len(results) == 2
        assert results[0].country == "US"
        assert results[0].year == 2020
        assert results[0].value == 828.7
        assert results[0].indicator_code == "mortality"

    @respx.mock
    @pytest.mark.asyncio
    async def test_invalid_xml(self, client: CDCWonderClient) -> None:
        respx.post(_CDC_URL).mock(return_value=Response(200, text="not xml"))
        results = await client.search_indicators("mortality")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_response(self, client: CDCWonderClient) -> None:
        respx.post(_CDC_URL).mock(
            return_value=Response(200, text='<?xml version="1.0"?><page></page>')
        )
        results = await client.search_indicators("mortality")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: CDCWonderClient) -> None:
        respx.post(_CDC_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="CDC WONDER"):
            await client.search_indicators("mortality")


# --- data.gov ---

_DATAGOV_URL = "https://catalog.data.gov/api/3/action/package_search"
_DATAGOV_RESPONSE = {
    "result": {
        "results": [
            {
                "id": "ds-001",
                "title": "Poverty Statistics",
                "organization": {"title": "Census Bureau"},
                "notes": "Annual poverty estimates by state",
                "tags": [{"name": "poverty"}, {"name": "census"}],
                "resources": [{"id": "r1"}, {"id": "r2"}],
                "metadata_modified": "2024-01-15",
            }
        ]
    }
}


class TestDataGovClient:
    @pytest.fixture
    def client(self) -> DataGovClient:
        return DataGovClient()

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_datasets(self, client: DataGovClient) -> None:
        respx.get(_DATAGOV_URL).mock(return_value=Response(200, json=_DATAGOV_RESPONSE))
        results = await client.search_datasets("poverty")
        assert len(results) == 1
        assert results[0].title == "Poverty Statistics"
        assert results[0].organization == "Census Bureau"
        assert results[0].tags == ("poverty", "census")
        assert results[0].resource_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: DataGovClient) -> None:
        respx.get(_DATAGOV_URL).mock(return_value=Response(200, json={"result": {"results": []}}))
        results = await client.search_datasets("nonexistent")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_organization(self, client: DataGovClient) -> None:
        respx.get(_DATAGOV_URL).mock(return_value=Response(200, json=_DATAGOV_RESPONSE))
        results = await client.search_datasets("poverty", organization="census-gov")
        assert len(results) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: DataGovClient) -> None:
        respx.get(_DATAGOV_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="data.gov"):
            await client.search_datasets("test")


# --- Retry Tests ---


class TestRetryBehavior:
    @respx.mock
    @pytest.mark.asyncio
    async def test_bls_rate_limit_retry(self) -> None:
        client = BLSClient(api_key="test")
        route = respx.post(_BLS_URL)
        route.side_effect = [
            Response(429),
            Response(200, json={"Results": {"series": []}}),
        ]
        results = await client.search_series("LNS14000000")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_usaspending_rate_limit_retry(self) -> None:
        client = USAspendingClient()
        route = respx.post(_USASPENDING_URL)
        route.side_effect = [
            Response(429),
            Response(200, json={"results": []}),
        ]
        results = await client.search_awards("test")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_census_rate_limit_retry(self) -> None:
        client = CensusClient(api_key="test")
        route = respx.get(_CENSUS_URL)
        route.side_effect = [
            Response(429),
            Response(200, json=_CENSUS_RESPONSE),
        ]
        results = await client.search_indicators("median_income")
        assert len(results) == 2

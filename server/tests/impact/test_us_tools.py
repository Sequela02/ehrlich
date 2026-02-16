"""Tests for US-specific Impact Evaluation tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.impact.domain.entities import (
    Benchmark,
    DatasetMetadata,
    EconomicSeries,
    EducationRecord,
    HealthIndicator,
    HousingData,
    SpendingRecord,
)
from ehrlich.impact.tools import (
    search_economic_indicators,
    search_education_data,
    search_health_indicators,
    search_housing_data,
    search_open_data,
    search_spending_data,
)


class TestSearchEconomicIndicatorsBLS:
    @pytest.mark.asyncio
    async def test_bls_source(self) -> None:
        series = [
            EconomicSeries(
                series_id="LNS14000000",
                title="LNS14000000",
                values=(),
                source="bls",
                unit="",
                frequency="",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_bls_data",
            new_callable=AsyncMock,
            return_value=series,
        ):
            result = json.loads(await search_economic_indicators("LNS14000000", source="bls"))
            assert result["source"] == "BLS"
            assert result["count"] == 1
            assert result["series"][0]["series_id"] == "LNS14000000"


class TestSearchEconomicIndicatorsCensus:
    @pytest.mark.asyncio
    async def test_census_source(self) -> None:
        benchmarks = [
            Benchmark(
                source="census",
                indicator="B19013_001E",
                value=78672.0,
                unit="",
                geography="California",
                period="2022",
                url="https://data.census.gov/table?q=B19013_001E",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_census_data",
            new_callable=AsyncMock,
            return_value=benchmarks,
        ):
            result = json.loads(await search_economic_indicators("median_income", source="census"))
            assert result["source"] == "Census"
            assert result["count"] == 1
            assert result["data"][0]["geography"] == "California"


class TestSearchHealthIndicators:
    @pytest.mark.asyncio
    async def test_who_source(self) -> None:
        indicators = [
            HealthIndicator(
                indicator_code="WHOSIS_000001",
                indicator_name="Life expectancy",
                country="MEX",
                year=2020,
                value=75.1,
                unit="years",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_health_data",
            new_callable=AsyncMock,
            return_value=indicators,
        ):
            result = json.loads(await search_health_indicators("WHOSIS_000001", source="who"))
            assert result["source"] == "WHO"
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_cdc_source(self) -> None:
        indicators = [
            HealthIndicator(
                indicator_code="mortality",
                indicator_name="2020",
                country="US",
                year=2020,
                value=828.7,
                unit="per 100,000",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_cdc_data",
            new_callable=AsyncMock,
            return_value=indicators,
        ):
            result = json.loads(await search_health_indicators("mortality", source="cdc"))
            assert result["source"] == "CDC WONDER"
            assert result["count"] == 1
            assert result["data"][0]["value"] == 828.7


class TestSearchSpendingData:
    @pytest.mark.asyncio
    async def test_returns_awards(self) -> None:
        records = [
            SpendingRecord(
                award_id="AWARD-001",
                recipient_name="Test University",
                amount=500000.0,
                agency="Department of Education",
                description="Grant",
                period="2023-01-01",
                award_type="Grant",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_spending_data",
            new_callable=AsyncMock,
            return_value=records,
        ):
            result = json.loads(await search_spending_data("education"))
            assert result["source"] == "USAspending"
            assert result["count"] == 1
            assert result["awards"][0]["recipient_name"] == "Test University"

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_spending_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_spending_data("nonexistent"))
            assert result["count"] == 0


class TestSearchEducationData:
    @pytest.mark.asyncio
    async def test_returns_schools(self) -> None:
        records = [
            EducationRecord(
                school_id="12345",
                name="Test University",
                state="CA",
                student_size=5000,
                net_price=15000.0,
                completion_rate=0.65,
                earnings_median=55000.0,
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_education_data",
            new_callable=AsyncMock,
            return_value=records,
        ):
            result = json.loads(await search_education_data("Test University", state="CA"))
            assert result["source"] == "College Scorecard"
            assert result["count"] == 1
            assert result["schools"][0]["name"] == "Test University"
            assert result["schools"][0]["completion_rate"] == 0.65


class TestSearchHousingData:
    @pytest.mark.asyncio
    async def test_returns_housing(self) -> None:
        records = [
            HousingData(
                area_name="Los Angeles",
                state="CA",
                fmr_0br=1200.0,
                fmr_1br=1500.0,
                fmr_2br=1900.0,
                fmr_3br=2400.0,
                fmr_4br=2800.0,
                median_income=75000.0,
                year=2024,
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_housing_data",
            new_callable=AsyncMock,
            return_value=records,
        ):
            result = json.loads(await search_housing_data("CA"))
            assert result["source"] == "HUD"
            assert result["count"] == 1
            assert result["data"][0]["fmr_2br"] == 1900.0


class TestSearchOpenData:
    @pytest.mark.asyncio
    async def test_returns_datasets(self) -> None:
        records = [
            DatasetMetadata(
                dataset_id="ds-001",
                title="Poverty Statistics",
                organization="Census Bureau",
                description="Annual poverty estimates",
                tags=("poverty", "census"),
                resource_count=2,
                modified="2024-01-15",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_open_data",
            new_callable=AsyncMock,
            return_value=records,
        ):
            result = json.loads(await search_open_data("poverty"))
            assert result["source"] == "data.gov"
            assert result["count"] == 1
            assert result["datasets"][0]["title"] == "Poverty Statistics"
            assert result["datasets"][0]["tags"] == ["poverty", "census"]

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_open_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_open_data("nonexistent"))
            assert result["count"] == 0

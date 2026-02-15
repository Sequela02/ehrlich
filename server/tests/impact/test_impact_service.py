"""Tests for ImpactService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ehrlich.impact.application.impact_service import ImpactService
from ehrlich.impact.domain.entities import (
    Benchmark,
    DataPoint,
    DatasetMetadata,
    EconomicSeries,
    EducationRecord,
    HealthIndicator,
    HousingData,
    SpendingRecord,
)


@pytest.fixture
def mock_economic() -> AsyncMock:
    mock = AsyncMock()
    mock.search_series = AsyncMock(
        return_value=[
            EconomicSeries(
                series_id="GDP",
                title="GDP",
                values=(),
                source="fred",
                unit="Billions",
                frequency="Quarterly",
            )
        ]
    )
    mock.get_series = AsyncMock(
        return_value=EconomicSeries(
            series_id="GDP",
            title="GDP",
            values=(DataPoint(date="2020-01-01", value=21481.0),),
            source="fred",
            unit="Billions",
            frequency="Quarterly",
        )
    )
    return mock


@pytest.fixture
def mock_health() -> AsyncMock:
    mock = AsyncMock()
    mock.search_indicators = AsyncMock(
        return_value=[
            HealthIndicator(
                indicator_code="WHOSIS_000001",
                indicator_name="Life expectancy",
                country="MEX",
                year=2020,
                value=75.1,
                unit="years",
            )
        ]
    )
    return mock


@pytest.fixture
def mock_development() -> AsyncMock:
    mock = AsyncMock()
    mock.search_indicators = AsyncMock(
        return_value=[
            Benchmark(
                source="world_bank",
                indicator="SE.PRM.ENRR",
                value=98.5,
                unit="",
                geography="Mexico",
                period="2020",
                url="https://data.worldbank.org/indicator/SE.PRM.ENRR",
            )
        ]
    )
    return mock


@pytest.fixture
def mock_spending() -> AsyncMock:
    mock = AsyncMock()
    mock.search_awards = AsyncMock(
        return_value=[
            SpendingRecord(
                award_id="AWARD-001",
                recipient_name="Test Org",
                amount=500000.0,
                agency="DOE",
                description="Grant",
                period="2023-01-01",
                award_type="Grant",
            )
        ]
    )
    return mock


@pytest.fixture
def mock_education() -> AsyncMock:
    mock = AsyncMock()
    mock.search_schools = AsyncMock(
        return_value=[
            EducationRecord(
                school_id="12345",
                name="Test U",
                state="CA",
                student_size=5000,
                net_price=15000.0,
                completion_rate=0.65,
                earnings_median=55000.0,
            )
        ]
    )
    return mock


@pytest.fixture
def mock_housing() -> AsyncMock:
    mock = AsyncMock()
    mock.search_housing_data = AsyncMock(
        return_value=[
            HousingData(
                area_name="LA",
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
    )
    return mock


@pytest.fixture
def mock_open_data() -> AsyncMock:
    mock = AsyncMock()
    mock.search_datasets = AsyncMock(
        return_value=[
            DatasetMetadata(
                dataset_id="ds-001",
                title="Poverty Stats",
                organization="Census",
                description="Poverty data",
                tags=("poverty",),
                resource_count=2,
                modified="2024-01-15",
            )
        ]
    )
    return mock


@pytest.fixture
def service(
    mock_economic: AsyncMock,
    mock_health: AsyncMock,
    mock_development: AsyncMock,
    mock_spending: AsyncMock,
    mock_education: AsyncMock,
    mock_housing: AsyncMock,
    mock_open_data: AsyncMock,
) -> ImpactService:
    return ImpactService(
        economic=mock_economic,
        health=mock_health,
        development=mock_development,
        spending=mock_spending,
        education=mock_education,
        housing=mock_housing,
        open_data=mock_open_data,
    )


class TestSearchEconomicData:
    @pytest.mark.asyncio
    async def test_returns_series(self, service: ImpactService) -> None:
        results = await service.search_economic_data("GDP")
        assert len(results) == 1
        assert results[0].series_id == "GDP"

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_economic_data("GDP")
        assert results == []


class TestGetEconomicSeries:
    @pytest.mark.asyncio
    async def test_returns_series(self, service: ImpactService) -> None:
        result = await service.get_economic_series("GDP")
        assert result is not None
        assert result.series_id == "GDP"
        assert len(result.values) == 1

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        result = await svc.get_economic_series("GDP")
        assert result is None


class TestSearchHealthData:
    @pytest.mark.asyncio
    async def test_returns_indicators(self, service: ImpactService) -> None:
        results = await service.search_health_data("WHOSIS_000001", country="MEX")
        assert len(results) == 1
        assert results[0].value == 75.1

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_health_data("WHOSIS_000001")
        assert results == []


class TestSearchDevelopmentData:
    @pytest.mark.asyncio
    async def test_returns_benchmarks(self, service: ImpactService) -> None:
        results = await service.search_development_data("SE.PRM.ENRR", country="MX")
        assert len(results) == 1
        assert results[0].value == 98.5

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_development_data("SE.PRM.ENRR")
        assert results == []


class TestFetchBenchmark:
    @pytest.mark.asyncio
    async def test_fred_source(self, service: ImpactService) -> None:
        results = await service.fetch_benchmark("GDP", "fred")
        assert len(results) == 1
        assert results[0]["source"] == "FRED"

    @pytest.mark.asyncio
    async def test_who_source(self, service: ImpactService) -> None:
        results = await service.fetch_benchmark(
            "WHOSIS_000001", "who", country="MEX", period="2019-2020"
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_worldbank_source(self, service: ImpactService) -> None:
        results = await service.fetch_benchmark(
            "SE.PRM.ENRR", "world_bank", country="MX", period="2019-2020"
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_unknown_source(self, service: ImpactService) -> None:
        results = await service.fetch_benchmark("X", "unknown")
        assert results == []


class TestComparePrograms:
    def test_two_group_comparison(self, service: ImpactService) -> None:
        programs = [
            {"name": "Treatment", "values": [85.0, 87.0, 89.0, 90.0, 88.0]},
            {"name": "Control", "values": [78.0, 78.5, 79.0, 78.8, 79.2]},
        ]
        result = service.compare_programs(programs, "enrollment_rate")
        assert result["metric"] == "enrollment_rate"
        assert "Treatment" in result["groups"]
        assert "Control" in result["groups"]
        assert "statistical_test" in result
        assert result["statistical_test"]["significant"] is True

    def test_single_group_no_test(self, service: ImpactService) -> None:
        programs = [{"name": "A", "values": [1.0, 2.0, 3.0]}]
        result = service.compare_programs(programs, "score")
        assert result["metric"] == "score"
        assert "statistical_test" not in result

    def test_empty_programs(self, service: ImpactService) -> None:
        result = service.compare_programs([], "score")
        assert result["metric"] == "score"
        assert result["groups"] == {}


class TestSearchSpendingData:
    @pytest.mark.asyncio
    async def test_returns_records(self, service: ImpactService) -> None:
        results = await service.search_spending_data("education")
        assert len(results) == 1
        assert results[0].award_id == "AWARD-001"

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_spending_data("education")
        assert results == []


class TestSearchEducationData:
    @pytest.mark.asyncio
    async def test_returns_records(self, service: ImpactService) -> None:
        results = await service.search_education_data("Test")
        assert len(results) == 1
        assert results[0].name == "Test U"

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_education_data("Test")
        assert results == []


class TestSearchHousingData:
    @pytest.mark.asyncio
    async def test_returns_records(self, service: ImpactService) -> None:
        results = await service.search_housing_data("CA")
        assert len(results) == 1
        assert results[0].fmr_2br == 1900.0

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_housing_data("CA")
        assert results == []


class TestSearchOpenData:
    @pytest.mark.asyncio
    async def test_returns_records(self, service: ImpactService) -> None:
        results = await service.search_open_data("poverty")
        assert len(results) == 1
        assert results[0].title == "Poverty Stats"

    @pytest.mark.asyncio
    async def test_no_repo(self) -> None:
        svc = ImpactService()
        results = await svc.search_open_data("poverty")
        assert results == []


class TestFetchBenchmarkExtended:
    @pytest.mark.asyncio
    async def test_bls_source(self) -> None:
        mock_bls = AsyncMock()
        mock_bls.search_series = AsyncMock(
            return_value=[
                EconomicSeries(
                    series_id="LNS14000000",
                    title="Unemployment",
                    values=(),
                    source="bls",
                    unit="",
                    frequency="",
                )
            ]
        )
        svc = ImpactService(bls=mock_bls)
        results = await svc.fetch_benchmark("LNS14000000", "bls")
        assert len(results) == 1
        assert results[0]["source"] == "BLS"

    @pytest.mark.asyncio
    async def test_census_source(self) -> None:
        mock_census = AsyncMock()
        mock_census.search_indicators = AsyncMock(
            return_value=[
                Benchmark(
                    source="census",
                    indicator="B19013_001E",
                    value=78672.0,
                    unit="",
                    geography="CA",
                    period="2022",
                    url="https://data.census.gov",
                )
            ]
        )
        svc = ImpactService(census=mock_census)
        results = await svc.fetch_benchmark("median_income", "census")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_cdc_source(self) -> None:
        mock_cdc = AsyncMock()
        mock_cdc.search_indicators = AsyncMock(
            return_value=[
                HealthIndicator(
                    indicator_code="mortality",
                    indicator_name="Mortality",
                    country="US",
                    year=2020,
                    value=828.7,
                    unit="per 100,000",
                )
            ]
        )
        svc = ImpactService(cdc=mock_cdc)
        results = await svc.fetch_benchmark("mortality", "cdc")
        assert len(results) == 1

"""Tests for ImpactService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ehrlich.impact.application.impact_service import ImpactService
from ehrlich.impact.domain.entities import (
    Benchmark,
    DataPoint,
    EconomicSeries,
    HealthIndicator,
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
def service(
    mock_economic: AsyncMock, mock_health: AsyncMock, mock_development: AsyncMock
) -> ImpactService:
    return ImpactService(economic=mock_economic, health=mock_health, development=mock_development)


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

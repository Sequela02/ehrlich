"""Tests for Impact Evaluation tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.impact.domain.entities import (
    Benchmark,
    EconomicSeries,
    HealthIndicator,
)
from ehrlich.impact.tools import (
    compare_programs,
    fetch_benchmark,
    search_economic_indicators,
)


class TestSearchEconomicIndicators:
    @pytest.mark.asyncio
    async def test_fred_source(self) -> None:
        series = [
            EconomicSeries(
                series_id="GDP",
                title="Gross Domestic Product",
                values=(),
                source="fred",
                unit="Billions",
                frequency="Quarterly",
            )
        ]
        with patch(
            "ehrlich.impact.tools._service.search_economic_data",
            new_callable=AsyncMock,
            return_value=series,
        ):
            result = json.loads(await search_economic_indicators("GDP", source="fred"))
            assert result["source"] == "FRED"
            assert result["count"] == 1
            assert result["series"][0]["series_id"] == "GDP"

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
            result = json.loads(
                await search_economic_indicators("WHOSIS_000001", source="who", country="MEX")
            )
            assert result["source"] == "WHO"
            assert result["count"] == 1
            assert result["data"][0]["value"] == 75.1

    @pytest.mark.asyncio
    async def test_worldbank_source(self) -> None:
        benchmarks = [
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
        with patch(
            "ehrlich.impact.tools._service.search_development_data",
            new_callable=AsyncMock,
            return_value=benchmarks,
        ):
            result = json.loads(
                await search_economic_indicators("SE.PRM.ENRR", source="world_bank", country="MX")
            )
            assert result["source"] == "World Bank"
            assert result["count"] == 1


class TestFetchBenchmark:
    @pytest.mark.asyncio
    async def test_returns_benchmarks(self) -> None:
        mock_result = [
            {"source": "FRED", "series_id": "GDP", "title": "GDP", "unit": "B", "frequency": "Q"}
        ]
        with patch(
            "ehrlich.impact.tools._service.fetch_benchmark",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = json.loads(await fetch_benchmark("GDP", source="fred"))
            assert result["indicator"] == "GDP"
            assert result["count"] == 1
            assert result["benchmarks"][0]["source"] == "FRED"

    @pytest.mark.asyncio
    async def test_empty_result(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.fetch_benchmark",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await fetch_benchmark("UNKNOWN", source="unknown"))
            assert result["count"] == 0


class TestComparePrograms:
    @pytest.mark.asyncio
    async def test_valid_comparison(self) -> None:
        mock_result = {
            "metric": "enrollment",
            "groups": {"A": {"n": 3, "mean": 2.0}, "B": {"n": 3, "mean": 1.0}},
            "statistical_test": {"test_name": "t_test", "p_value": 0.01, "significant": True},
        }
        with patch(
            "ehrlich.impact.tools._service.compare_programs",
            return_value=mock_result,
        ):
            programs_json = json.dumps(
                [
                    {"name": "A", "values": [1.0, 2.0, 3.0]},
                    {"name": "B", "values": [0.5, 1.0, 1.5]},
                ]
            )
            result = json.loads(await compare_programs(programs_json, "enrollment"))
            assert result["metric"] == "enrollment"
            assert "statistical_test" in result

    @pytest.mark.asyncio
    async def test_invalid_json(self) -> None:
        result = json.loads(await compare_programs("not json", "metric"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_not_array(self) -> None:
        result = json.loads(await compare_programs('{"name": "A"}', "metric"))
        assert "error" in result

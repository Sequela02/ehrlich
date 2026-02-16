"""Tests for impact evaluation visualization tools."""

from __future__ import annotations

import json

import pytest

from ehrlich.investigation.tools_viz import (
    render_geographic_comparison,
    render_parallel_trends,
    render_program_dashboard,
)


class TestRenderProgramDashboard:
    @pytest.mark.anyio
    async def test_basic(self) -> None:
        result = json.loads(
            await render_program_dashboard(
                indicators=[
                    {
                        "name": "Enrollment",
                        "baseline": 70.0,
                        "target": 90.0,
                        "actual": 85.0,
                        "unit": "%",
                    },
                    {
                        "name": "Attendance",
                        "baseline": 60.0,
                        "target": 80.0,
                        "actual": 35.0,
                        "unit": "%",
                    },
                ],
                program_name="Prospera",
            )
        )
        assert result["viz_type"] == "program_dashboard"
        assert result["data"]["program_name"] == "Prospera"
        assert len(result["data"]["indicators"]) == 2
        assert result["data"]["indicators"][0]["status"] == "on_track"
        assert result["data"]["indicators"][1]["status"] == "off_track"

    @pytest.mark.anyio
    async def test_empty_indicators(self) -> None:
        result = json.loads(await render_program_dashboard(indicators=[]))
        assert result["viz_type"] == "program_dashboard"
        assert result["data"]["indicators"] == []

    @pytest.mark.anyio
    async def test_custom_title(self) -> None:
        result = json.loads(
            await render_program_dashboard(
                indicators=[{"name": "X", "baseline": 0, "target": 10, "actual": 7, "unit": "pts"}],
                title="Custom Title",
            )
        )
        assert result["title"] == "Custom Title"


class TestRenderGeographicComparison:
    @pytest.mark.anyio
    async def test_basic(self) -> None:
        result = json.loads(
            await render_geographic_comparison(
                regions=[
                    {"name": "Mexico", "value": 85.2},
                    {"name": "Brazil", "value": 92.1},
                    {"name": "Colombia", "value": 78.5},
                ],
                metric_name="Enrollment Rate",
                benchmark=88.0,
            )
        )
        assert result["viz_type"] == "geographic_comparison"
        assert len(result["data"]["regions"]) == 3
        assert result["data"]["benchmark"] == 88.0
        assert result["data"]["metric_name"] == "Enrollment Rate"

    @pytest.mark.anyio
    async def test_no_benchmark(self) -> None:
        result = json.loads(
            await render_geographic_comparison(
                regions=[{"name": "A", "value": 10.0}],
            )
        )
        assert result["data"]["benchmark"] is None

    @pytest.mark.anyio
    async def test_empty_regions(self) -> None:
        result = json.loads(await render_geographic_comparison(regions=[]))
        assert result["data"]["regions"] == []


class TestRenderParallelTrends:
    @pytest.mark.anyio
    async def test_basic(self) -> None:
        result = json.loads(
            await render_parallel_trends(
                treatment_series=[
                    {"period": "2010", "value": 70.0},
                    {"period": "2011", "value": 72.0},
                    {"period": "2012", "value": 80.0},
                    {"period": "2013", "value": 85.0},
                ],
                control_series=[
                    {"period": "2010", "value": 70.0},
                    {"period": "2011", "value": 71.0},
                    {"period": "2012", "value": 72.0},
                    {"period": "2013", "value": 73.0},
                ],
                treatment_start="2012",
            )
        )
        assert result["viz_type"] == "parallel_trends"
        assert len(result["data"]["treatment"]) == 4
        assert len(result["data"]["control"]) == 4
        assert result["data"]["treatment_start"] == "2012"

    @pytest.mark.anyio
    async def test_empty_series(self) -> None:
        result = json.loads(
            await render_parallel_trends(
                treatment_series=[],
                control_series=[],
            )
        )
        assert result["data"]["treatment"] == []
        assert result["data"]["control"] == []

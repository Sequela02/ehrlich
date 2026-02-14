"""Tests for causal inference tool functions."""

from __future__ import annotations

import json

import pytest

from ehrlich.analysis.tools import (
    assess_threats,
    compute_cost_effectiveness,
    estimate_did,
    estimate_psm,
    estimate_rdd,
    estimate_synthetic_control,
)


class TestEstimateDidTool:
    @pytest.mark.anyio
    async def test_valid_input(self) -> None:
        result = json.loads(
            await estimate_did(
                treatment_pre="[80.0, 81.0, 79.5, 80.5, 80.0]",
                treatment_post="[86.0, 87.0, 85.5, 86.5, 86.0]",
                control_pre="[80.0, 81.0, 79.5, 80.5, 80.0]",
                control_post="[81.0, 82.0, 80.5, 81.5, 81.0]",
            )
        )

        assert result["method"] == "difference_in_differences"
        assert "effect_size" in result
        assert "p_value" in result
        assert len(result["confidence_interval"]) == 2
        assert isinstance(result["assumptions"], list)
        assert isinstance(result["threats"], list)

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await estimate_did("not json", "[1]", "[1]", "[1]"))
        assert "error" in result

    @pytest.mark.anyio
    async def test_empty_arrays(self) -> None:
        result = json.loads(await estimate_did("[]", "[1, 2]", "[1, 2]", "[1, 2]"))
        assert "error" in result


class TestEstimatePsmTool:
    @pytest.mark.anyio
    async def test_valid_input(self) -> None:
        result = json.loads(
            await estimate_psm(
                treated_outcomes="[90.0, 92.0, 88.0, 91.0]",
                control_outcomes="[80.0, 82.0, 78.0, 81.0]",
                treated_covariates="[[1.0, 2.0], [1.5, 2.5], [1.2, 2.2], [1.8, 2.8]]",
                control_covariates="[[0.9, 1.9], [1.4, 2.4], [1.1, 2.1], [1.7, 2.7]]",
            )
        )

        assert result["method"] == "propensity_score_matching"
        assert "effect_size" in result
        assert isinstance(result["threats"], list)

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await estimate_psm("bad", "[1]", "[[1]]", "[[1]]"))
        assert "error" in result


class TestEstimateRddTool:
    @pytest.mark.anyio
    async def test_valid_input(self) -> None:
        result = json.loads(
            await estimate_rdd(
                running_variable="[40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60]",
                outcome="[48, 49, 50, 51, 52, 70, 71, 72, 73, 74, 75]",
                cutoff=50.0,
            )
        )

        assert "regression_discontinuity" in result["method"]
        assert "effect_size" in result

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await estimate_rdd("bad", "[1]", cutoff=50.0))
        assert "error" in result

    @pytest.mark.anyio
    async def test_mismatched_lengths(self) -> None:
        result = json.loads(await estimate_rdd("[1, 2, 3]", "[1, 2]", cutoff=2.0))
        assert "error" in result


class TestEstimateSyntheticControlTool:
    @pytest.mark.anyio
    async def test_valid_input(self) -> None:
        result = json.loads(
            await estimate_synthetic_control(
                treated_series="[10, 11, 12, 25, 26, 27]",
                donor_matrix="[[10, 11, 12, 13, 14, 15], [9, 10, 11, 12, 13, 14]]",
                treatment_period=3,
            )
        )

        assert result["method"] == "synthetic_control"
        assert "effect_size" in result

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await estimate_synthetic_control("bad", "[[1]]", treatment_period=1))
        assert "error" in result


class TestAssessThreatsTool:
    @pytest.mark.anyio
    async def test_did_threats(self) -> None:
        result = json.loads(
            await assess_threats(
                method="did",
                sample_sizes='{"treatment": 50, "control": 45}',
                parallel_trends_p=0.03,
                effect_size=0.5,
            )
        )

        assert result["method"] == "did"
        assert isinstance(result["threats"], list)
        threat_types = [t["type"] for t in result["threats"]]
        assert "parallel_trends_violation" in threat_types

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await assess_threats(method="did", sample_sizes="not json"))
        assert "error" in result

    @pytest.mark.anyio
    async def test_psm_threats(self) -> None:
        result = json.loads(
            await assess_threats(
                method="psm",
                sample_sizes='{"treatment": 100, "control": 100}',
            )
        )
        threat_types = [t["type"] for t in result["threats"]]
        assert "unobserved_confounders" in threat_types

    @pytest.mark.anyio
    async def test_rdd_threats(self) -> None:
        result = json.loads(
            await assess_threats(
                method="rdd",
                sample_sizes='{"treatment": 100, "control": 100}',
            )
        )
        threat_types = [t["type"] for t in result["threats"]]
        assert "manipulation" in threat_types


class TestComputeCostEffectivenessTool:
    @pytest.mark.anyio
    async def test_basic(self) -> None:
        result = json.loads(
            await compute_cost_effectiveness(
                program_name="Test",
                total_cost=100000.0,
                total_effect=500.0,
            )
        )

        assert result["program_name"] == "Test"
        assert result["cost_per_unit"] == 200.0
        assert result["icer"] is None

    @pytest.mark.anyio
    async def test_with_icer(self) -> None:
        result = json.loads(
            await compute_cost_effectiveness(
                program_name="A",
                total_cost=200000.0,
                total_effect=800.0,
                comparison_cost=100000.0,
                comparison_effect=500.0,
            )
        )

        assert result["icer"] is not None

"""Tests for DiD and threat assessment tool functions."""

from __future__ import annotations

import json

import pytest

from ehrlich.impact.tools import assess_threats, estimate_did


class TestEstimateDidTool:
    @pytest.mark.anyio
    async def test_valid_input(self) -> None:
        result = json.loads(await estimate_did(
            treatment_pre="[80.0, 81.0, 79.5, 80.5, 80.0]",
            treatment_post="[86.0, 87.0, 85.5, 86.5, 86.0]",
            control_pre="[80.0, 81.0, 79.5, 80.5, 80.0]",
            control_post="[81.0, 82.0, 80.5, 81.5, 81.0]",
        ))

        assert result["method"] == "difference_in_differences"
        assert "effect_size" in result
        assert "p_value" in result
        assert "confidence_interval" in result
        assert len(result["confidence_interval"]) == 2
        assert "threats" in result
        assert "evidence_tier" in result
        assert isinstance(result["assumptions"], list)

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await estimate_did(
            treatment_pre="not json",
            treatment_post="[1, 2]",
            control_pre="[1, 2]",
            control_post="[1, 2]",
        ))
        assert "error" in result

    @pytest.mark.anyio
    async def test_empty_arrays(self) -> None:
        result = json.loads(await estimate_did(
            treatment_pre="[]",
            treatment_post="[1, 2]",
            control_pre="[1, 2]",
            control_post="[1, 2]",
        ))
        assert "error" in result

    @pytest.mark.anyio
    async def test_identical_groups(self) -> None:
        result = json.loads(await estimate_did(
            treatment_pre="[10, 11, 10.5]",
            treatment_post="[10, 11, 10.5]",
            control_pre="[10, 11, 10.5]",
            control_post="[10, 11, 10.5]",
        ))
        assert abs(result["effect_size"]) < 0.01


class TestAssessThreatsTool:
    @pytest.mark.anyio
    async def test_did_threats(self) -> None:
        result = json.loads(await assess_threats(
            method="did",
            sample_sizes='{"treatment": 50, "control": 45}',
            parallel_trends_p=0.03,
            effect_size=0.5,
        ))

        assert result["method"] == "did"
        assert isinstance(result["threats"], list)
        threat_types = [t["type"] for t in result["threats"]]
        assert "parallel_trends_violation" in threat_types

    @pytest.mark.anyio
    async def test_small_sample(self) -> None:
        result = json.loads(await assess_threats(
            method="rct",
            sample_sizes='{"treatment": 3, "control": 4}',
        ))

        threat_types = [t["type"] for t in result["threats"]]
        assert "small_sample" in threat_types

    @pytest.mark.anyio
    async def test_invalid_json(self) -> None:
        result = json.loads(await assess_threats(
            method="did",
            sample_sizes="not json",
        ))
        assert "error" in result

    @pytest.mark.anyio
    async def test_psm_threats(self) -> None:
        result = json.loads(await assess_threats(
            method="psm",
            sample_sizes='{"treatment": 100, "control": 100}',
        ))

        threat_types = [t["type"] for t in result["threats"]]
        assert "unobserved_confounders" in threat_types

    @pytest.mark.anyio
    async def test_rdd_threats(self) -> None:
        result = json.loads(await assess_threats(
            method="rdd",
            sample_sizes='{"treatment": 100, "control": 100}',
        ))

        threat_types = [t["type"] for t in result["threats"]]
        assert "manipulation" in threat_types

    @pytest.mark.anyio
    async def test_large_effect_threat(self) -> None:
        result = json.loads(await assess_threats(
            method="rct",
            sample_sizes='{"treatment": 100, "control": 100}',
            effect_size=3.5,
        ))

        threat_types = [t["type"] for t in result["threats"]]
        assert "implausible_effect" in threat_types

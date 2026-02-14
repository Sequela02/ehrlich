"""Tests for causal inference domain entities."""

from __future__ import annotations

from ehrlich.analysis.domain.causal import (
    CausalEstimate,
    CostEffectivenessResult,
    ThreatToValidity,
)


class TestThreatToValidity:
    def test_construction(self) -> None:
        threat = ThreatToValidity(
            type="small_sample",
            severity="high",
            description="N < 5",
            mitigation="Increase N",
        )
        assert threat.type == "small_sample"
        assert threat.severity == "high"

    def test_frozen(self) -> None:
        threat = ThreatToValidity(type="a", severity="low", description="b", mitigation="c")
        try:
            threat.type = "x"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestCausalEstimate:
    def test_construction(self) -> None:
        estimate = CausalEstimate(
            method="did",
            effect_size=5.0,
            standard_error=1.0,
            confidence_interval=(3.04, 6.96),
            p_value=0.001,
            n_treatment=50,
            n_control=50,
            covariates=(),
            assumptions=("Parallel trends",),
            threats=(),
            evidence_tier="moderate",
        )
        assert estimate.method == "did"
        assert estimate.effect_size == 5.0
        assert len(estimate.confidence_interval) == 2


class TestCostEffectivenessResult:
    def test_construction(self) -> None:
        result = CostEffectivenessResult(
            program_name="Test Program",
            total_cost=100000.0,
            total_effect=500.0,
            cost_per_unit=200.0,
            currency="USD",
            effect_unit="enrollees",
            icer=None,
        )
        assert result.program_name == "Test Program"
        assert result.cost_per_unit == 200.0
        assert result.icer is None

    def test_with_icer(self) -> None:
        result = CostEffectivenessResult(
            program_name="A",
            total_cost=200000.0,
            total_effect=800.0,
            cost_per_unit=250.0,
            currency="USD",
            effect_unit="QALYs",
            icer=150.0,
        )
        assert result.icer == 150.0

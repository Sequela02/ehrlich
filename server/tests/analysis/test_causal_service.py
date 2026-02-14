"""Tests for CausalService."""

from __future__ import annotations

import pytest

from ehrlich.analysis.application.causal_service import CausalService


@pytest.fixture
def service() -> CausalService:
    return CausalService()


class TestAssessThreats:
    def test_small_sample_high(self, service: CausalService) -> None:
        threats = service.assess_threats("did", {"treatment": 3, "control": 4})
        assert any(t.severity == "high" and t.type == "small_sample" for t in threats)

    def test_small_sample_medium(self, service: CausalService) -> None:
        threats = service.assess_threats("did", {"treatment": 20, "control": 15})
        assert any(t.severity == "medium" and t.type == "small_sample" for t in threats)

    def test_parallel_trends_violation(self, service: CausalService) -> None:
        threats = service.assess_threats("did", {"t": 50, "c": 50}, parallel_trends_p=0.03)
        assert any(t.type == "parallel_trends_violation" for t in threats)

    def test_psm_unobserved(self, service: CausalService) -> None:
        threats = service.assess_threats("psm", {"t": 100, "c": 100})
        assert any(t.type == "unobserved_confounders" for t in threats)

    def test_rdd_manipulation(self, service: CausalService) -> None:
        threats = service.assess_threats("rdd", {"t": 100, "c": 100})
        assert any(t.type == "manipulation" for t in threats)

    def test_synthetic_control(self, service: CausalService) -> None:
        threats = service.assess_threats("synthetic_control", {"t": 100, "c": 10})
        assert any(t.type == "convex_hull" for t in threats)

    def test_implausible_effect(self, service: CausalService) -> None:
        threats = service.assess_threats("rct", {"t": 100, "c": 100}, effect_size=3.5)
        assert any(t.type == "implausible_effect" for t in threats)

    def test_large_sample_no_sample_threat(self, service: CausalService) -> None:
        threats = service.assess_threats("rct", {"t": 100, "c": 100})
        assert not any(t.type == "small_sample" for t in threats)


class TestComputeCostEffectiveness:
    def test_basic(self, service: CausalService) -> None:
        result = CausalService.compute_cost_effectiveness(
            program_name="Test",
            total_cost=100000.0,
            total_effect=500.0,
        )
        assert result.cost_per_unit == 200.0
        assert result.icer is None

    def test_with_icer(self, service: CausalService) -> None:
        result = CausalService.compute_cost_effectiveness(
            program_name="A",
            total_cost=200000.0,
            total_effect=800.0,
            comparison_cost=100000.0,
            comparison_effect=500.0,
        )
        # ICER = (200000-100000) / (800-500) = 333.33
        assert result.icer is not None
        assert abs(result.icer - 333.33) < 0.01

    def test_zero_effect(self, service: CausalService) -> None:
        result = CausalService.compute_cost_effectiveness(
            program_name="Zero",
            total_cost=100000.0,
            total_effect=0.0,
        )
        assert result.cost_per_unit == 0.0

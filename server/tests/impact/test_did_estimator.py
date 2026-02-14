"""Tests for the DiD estimator infrastructure."""

from __future__ import annotations

import pytest

from ehrlich.impact.infrastructure.did_estimator import DiDEstimator


@pytest.fixture
def estimator() -> DiDEstimator:
    return DiDEstimator()


class TestDiDEstimator:
    def test_known_effect(self, estimator: DiDEstimator) -> None:
        """Synthetic data with known true DiD effect of ~5.0."""
        treatment_pre = [80.0, 81.0, 79.5, 80.5, 80.0]
        treatment_post = [86.0, 87.0, 85.5, 86.5, 86.0]  # +6
        control_pre = [80.0, 81.0, 79.5, 80.5, 80.0]
        control_post = [81.0, 82.0, 80.5, 81.5, 81.0]  # +1

        result = estimator.estimate_did(treatment_pre, treatment_post, control_pre, control_post)

        assert result.method == "difference_in_differences"
        assert abs(result.effect_size - 5.0) < 0.01
        assert result.p_value < 0.05
        assert result.confidence_interval[0] < result.effect_size < result.confidence_interval[1]
        assert result.n_treatment == 10
        assert result.n_control == 10

    def test_no_effect(self, estimator: DiDEstimator) -> None:
        """Both groups change equally -- no causal effect."""
        treatment_pre = [50.0, 51.0, 49.5, 50.5]
        treatment_post = [52.0, 53.0, 51.5, 52.5]  # +2
        control_pre = [50.0, 51.0, 49.5, 50.5]
        control_post = [52.0, 53.0, 51.5, 52.5]  # +2

        result = estimator.estimate_did(treatment_pre, treatment_post, control_pre, control_post)

        assert abs(result.effect_size) < 0.01
        assert result.p_value > 0.05

    def test_large_effect(self, estimator: DiDEstimator) -> None:
        """Large treatment effect triggers implausible_effect threat."""
        treatment_pre = [10.0, 11.0, 10.5]
        treatment_post = [30.0, 31.0, 30.5]  # +20
        control_pre = [10.0, 11.0, 10.5]
        control_post = [11.0, 12.0, 11.5]  # +1

        result = estimator.estimate_did(treatment_pre, treatment_post, control_pre, control_post)

        assert result.effect_size > 15.0
        threat_types = [t.type for t in result.threats]
        assert "implausible_effect" in threat_types

    def test_small_sample_threat(self, estimator: DiDEstimator) -> None:
        """Very small samples trigger small_sample threat."""
        result = estimator.estimate_did([10.0, 11.0], [15.0, 16.0], [10.0, 11.0], [11.0, 12.0])

        threat_types = [t.type for t in result.threats]
        assert "small_sample" in threat_types

    def test_parallel_trends_violation(self, estimator: DiDEstimator) -> None:
        """Clearly different pre-treatment trends trigger parallel_trends threat."""
        treatment_pre = [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0]
        control_pre = [50.0, 50.5, 51.0, 51.5, 52.0, 52.5, 53.0, 53.5]
        treatment_post = [90.0, 95.0]
        control_post = [54.0, 54.5]

        result = estimator.estimate_did(treatment_pre, treatment_post, control_pre, control_post)

        threat_types = [t.type for t in result.threats]
        assert "parallel_trends_violation" in threat_types or "parallel_trends_weak" in threat_types

    def test_evidence_tier_classification(self, estimator: DiDEstimator) -> None:
        """DiD without severe threats should be classified as moderate."""
        treatment_pre = [80.0, 81.0, 79.5, 80.5, 80.0, 79.8, 80.2, 81.5]
        treatment_post = [86.0, 87.0, 85.5, 86.5, 86.0, 85.8, 86.2, 87.5]
        control_pre = [80.0, 81.0, 79.5, 80.5, 80.0, 79.8, 80.2, 81.5]
        control_post = [81.0, 82.0, 80.5, 81.5, 81.0, 80.8, 81.2, 82.5]

        result = estimator.estimate_did(treatment_pre, treatment_post, control_pre, control_post)

        assert result.evidence_tier in ("moderate", "strong")

    def test_assumptions_present(self, estimator: DiDEstimator) -> None:
        result = estimator.estimate_did(
            [10.0, 11.0, 12.0], [15.0, 16.0, 17.0],
            [10.0, 11.0, 12.0], [11.0, 12.0, 13.0],
        )
        assert len(result.assumptions) == 4
        assert "Parallel trends" in result.assumptions

    def test_identical_groups(self, estimator: DiDEstimator) -> None:
        """All groups identical -- no effect, high p-value."""
        vals = [10.0, 11.0, 10.5, 10.8]
        result = estimator.estimate_did(vals, vals, vals, vals)
        assert abs(result.effect_size) < 0.01

    def test_single_values(self, estimator: DiDEstimator) -> None:
        """Minimal input: single value per group."""
        result = estimator.estimate_did([10.0], [15.0], [10.0], [11.0])
        assert abs(result.effect_size - 4.0) < 0.01

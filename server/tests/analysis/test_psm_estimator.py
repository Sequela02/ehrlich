"""Tests for the PSM estimator."""

from __future__ import annotations

import pytest

from ehrlich.analysis.infrastructure.psm_estimator import PSMEstimator


@pytest.fixture
def estimator() -> PSMEstimator:
    return PSMEstimator()


class TestPSMEstimator:
    def test_known_att(self, estimator: PSMEstimator) -> None:
        """Treatment group has clearly higher outcomes."""
        treated_out = [90.0, 92.0, 88.0, 91.0, 89.0, 93.0, 87.0, 90.0]
        control_out = [80.0, 82.0, 78.0, 81.0, 79.0, 83.0, 77.0, 80.0]
        treated_cov = [[i * 0.1, i * 0.2] for i in range(8)]
        control_cov = [[i * 0.1 + 0.05, i * 0.2 + 0.1] for i in range(8)]

        result = estimator.estimate(treated_out, control_out, treated_cov, control_cov)

        assert result.method == "propensity_score_matching"
        assert result.effect_size > 5.0
        assert result.n_treatment > 0
        assert len(result.assumptions) == 4

    def test_no_effect(self, estimator: PSMEstimator) -> None:
        """Both groups have identical outcomes."""
        outcomes = [50.0, 51.0, 49.5, 50.5, 50.2, 50.8, 49.8, 51.2]
        covariates = [[i * 0.1, i * 0.2] for i in range(8)]

        result = estimator.estimate(outcomes, outcomes, covariates, covariates)

        assert abs(result.effect_size) < 1.0

    def test_unobserved_confounders_threat(self, estimator: PSMEstimator) -> None:
        """PSM always has unobserved confounders threat."""
        treated_out = [10.0, 12.0, 11.0, 13.0]
        control_out = [8.0, 9.0, 7.0, 10.0]
        treated_cov = [[1.0], [2.0], [1.5], [2.5]]
        control_cov = [[0.8], [1.8], [1.3], [2.3]]

        result = estimator.estimate(treated_out, control_out, treated_cov, control_cov)
        threat_types = [t.type for t in result.threats]
        assert "unobserved_confounders" in threat_types

    def test_poor_overlap(self, estimator: PSMEstimator) -> None:
        """Very different covariates should trigger overlap issues."""
        treated_out = [90.0, 92.0, 88.0, 91.0]
        control_out = [80.0, 82.0, 78.0, 81.0]
        treated_cov = [[100.0, 200.0]] * 4
        control_cov = [[1.0, 2.0]] * 4

        result = estimator.estimate(treated_out, control_out, treated_cov, control_cov)
        # Should still produce a result (may have poor overlap threat)
        assert result.method == "propensity_score_matching"

    def test_small_sample(self, estimator: PSMEstimator) -> None:
        """Very small samples may result in few matches."""
        result = estimator.estimate(
            [10.0, 12.0],
            [8.0, 9.0],
            [[1.0], [2.0]],
            [[0.8], [1.8]],
        )
        assert result.method == "propensity_score_matching"

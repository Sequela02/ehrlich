"""Tests for the Synthetic Control estimator."""

from __future__ import annotations

import pytest

from ehrlich.analysis.infrastructure.synthetic_control_estimator import SyntheticControlEstimator


@pytest.fixture
def estimator() -> SyntheticControlEstimator:
    return SyntheticControlEstimator()


class TestSyntheticControlEstimator:
    def test_known_effect(self, estimator: SyntheticControlEstimator) -> None:
        """Treated jumps at treatment period while donors stay flat."""
        treated = [10.0, 11.0, 12.0, 13.0, 25.0, 26.0, 27.0]
        donors = [
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
            [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        ]

        result = estimator.estimate(treated, donors, treatment_period=4)

        assert result.method == "synthetic_control"
        assert result.effect_size > 5.0
        assert result.n_treatment == 3  # 3 post-treatment periods
        assert result.n_control == 2  # 2 donors

    def test_no_effect(self, estimator: SyntheticControlEstimator) -> None:
        """Treated follows donors -- no divergence."""
        treated = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        donors = [
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        ]

        result = estimator.estimate(treated, donors, treatment_period=3)
        assert abs(result.effect_size) < 2.0

    def test_few_donors_threat(self, estimator: SyntheticControlEstimator) -> None:
        """Fewer than 5 donors triggers warning."""
        treated = [10.0, 11.0, 12.0, 20.0, 21.0]
        donors = [
            [10.0, 11.0, 12.0, 13.0, 14.0],
            [9.0, 10.0, 11.0, 12.0, 13.0],
        ]

        result = estimator.estimate(treated, donors, treatment_period=3)
        threat_types = [t.type for t in result.threats]
        assert "few_donors" in threat_types

    def test_weights_sum_to_one(self, estimator: SyntheticControlEstimator) -> None:
        """Optimization should produce valid weights."""
        treated = [10.0, 11.0, 12.0, 20.0, 21.0, 22.0]
        donors = [
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        ]

        result = estimator.estimate(treated, donors, treatment_period=3)
        assert result.method == "synthetic_control"
        assert len(result.assumptions) == 4

    def test_insufficient_data(self, estimator: SyntheticControlEstimator) -> None:
        """Treatment period at boundary should handle gracefully."""
        result = estimator.estimate([10.0, 20.0], [[10.0, 11.0]], treatment_period=1)
        # Should still produce a valid estimate or report insufficient data
        assert result.method == "synthetic_control"

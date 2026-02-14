"""Tests for the RDD estimator."""

from __future__ import annotations

import pytest

from ehrlich.analysis.infrastructure.rdd_estimator import RDDEstimator


@pytest.fixture
def estimator() -> RDDEstimator:
    return RDDEstimator()


class TestRDDEstimator:
    def test_sharp_discontinuity(self, estimator: RDDEstimator) -> None:
        """Clear jump at cutoff in sharp design."""
        # Below cutoff: outcome ~ 50, above cutoff: outcome ~ 70
        x = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0]
        y = [48.0, 49.0, 50.0, 51.0, 52.0, 70.0, 71.0, 72.0, 73.0, 74.0, 75.0]

        result = estimator.estimate(x, y, cutoff=50.0)

        assert "regression_discontinuity" in result.method
        assert result.effect_size > 10.0
        assert result.n_treatment >= 1
        assert result.n_control >= 1

    def test_no_discontinuity(self, estimator: RDDEstimator) -> None:
        """Smooth function with no jump."""
        x = [float(i) for i in range(20, 80)]
        y = [float(i) * 0.5 + 10.0 for i in range(20, 80)]

        result = estimator.estimate(x, y, cutoff=50.0)

        assert abs(result.effect_size) < 5.0

    def test_fuzzy_design(self, estimator: RDDEstimator) -> None:
        """Fuzzy design should still produce a result."""
        x = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0]
        y = [48.0, 49.0, 50.0, 51.0, 52.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0]

        result = estimator.estimate(x, y, cutoff=50.0, design="fuzzy")

        assert "fuzzy" in result.method
        assert result.effect_size != 0.0

    def test_custom_bandwidth(self, estimator: RDDEstimator) -> None:
        """With explicit bandwidth."""
        x = [float(i) for i in range(20, 80)]
        y = [50.0 if i < 50 else 70.0 for i in range(20, 80)]

        result = estimator.estimate(x, y, cutoff=50.0, bandwidth=10.0)
        assert result.effect_size > 10.0

    def test_insufficient_data(self, estimator: RDDEstimator) -> None:
        """Too few observations should trigger insufficient_data threat."""
        result = estimator.estimate([49.0], [50.0, 51.0], cutoff=50.0, bandwidth=5.0)
        threat_types = [t.type for t in result.threats]
        assert "insufficient_data" in threat_types or "small_bandwidth" in threat_types

    def test_assumptions_present(self, estimator: RDDEstimator) -> None:
        x = [float(i) for i in range(40, 62)]
        y = [50.0 if i < 50 else 70.0 for i in range(40, 62)]
        result = estimator.estimate(x, y, cutoff=50.0)
        assert len(result.assumptions) == 4
        assert "Continuity at cutoff" in result.assumptions

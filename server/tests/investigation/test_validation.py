from __future__ import annotations

from ehrlich.investigation.domain.validation import compute_z_prime


class TestZPrime:
    def test_excellent_separation(self) -> None:
        positive = [0.9, 0.85, 0.92, 0.88, 0.91]
        negative = [0.1, 0.15, 0.08, 0.12, 0.09]
        result = compute_z_prime(positive, negative)
        assert result.z_prime is not None
        assert result.z_prime >= 0.5
        assert result.quality == "excellent"

    def test_marginal_separation(self) -> None:
        positive = [0.6, 0.55, 0.65, 0.58, 0.62]
        negative = [0.35, 0.40, 0.30, 0.38, 0.33]
        result = compute_z_prime(positive, negative)
        assert result.z_prime is not None
        assert 0.0 < result.z_prime < 0.5
        assert result.quality == "marginal"

    def test_no_separation(self) -> None:
        positive = [0.5, 0.3, 0.7, 0.2, 0.8]
        negative = [0.4, 0.6, 0.5, 0.3, 0.7]
        result = compute_z_prime(positive, negative)
        assert result.z_prime is not None
        assert result.z_prime <= 0.0
        assert result.quality == "unusable"

    def test_insufficient_controls(self) -> None:
        result = compute_z_prime([0.9, 0.8], [0.1, 0.2])
        assert result.z_prime is None
        assert result.quality == "insufficient"
        assert result.positive_count == 2
        assert result.negative_count == 2

    def test_identical_means(self) -> None:
        positive = [0.5, 0.5, 0.5]
        negative = [0.5, 0.5, 0.5]
        result = compute_z_prime(positive, negative)
        assert result.z_prime == 0.0
        assert result.quality == "unusable"

    def test_perfect_separation(self) -> None:
        positive = [1.0, 1.0, 1.0]
        negative = [0.0, 0.0, 0.0]
        result = compute_z_prime(positive, negative)
        assert result.z_prime is not None
        assert result.z_prime == 1.0
        assert result.quality == "excellent"

    def test_custom_min_controls(self) -> None:
        result = compute_z_prime([0.9, 0.8, 0.85], [0.1, 0.2, 0.15], min_controls=5)
        assert result.z_prime is None
        assert result.quality == "insufficient"

    def test_single_element_groups_insufficient(self) -> None:
        result = compute_z_prime([0.9], [0.1])
        assert result.z_prime is None
        assert result.quality == "insufficient"

    def test_returns_correct_stats(self) -> None:
        positive = [0.9, 0.9, 0.9]
        negative = [0.1, 0.1, 0.1]
        result = compute_z_prime(positive, negative)
        assert result.positive_mean == 0.9
        assert result.negative_mean == 0.1
        assert result.positive_count == 3
        assert result.negative_count == 3

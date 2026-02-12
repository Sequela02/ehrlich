from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev


@dataclass(frozen=True)
class AssayQualityMetrics:
    z_prime: float | None
    quality: str
    positive_mean: float
    positive_std: float
    negative_mean: float
    negative_std: float
    positive_count: int
    negative_count: int


def compute_z_prime(
    positive_scores: list[float],
    negative_scores: list[float],
    min_controls: int = 3,
) -> AssayQualityMetrics:
    """Compute Z'-factor assay quality metric.

    Formula: Z' = 1 - (3*sigma_pos + 3*sigma_neg) / |mu_pos - mu_neg|

    Thresholds (Zhang et al., 1999):
      >= 0.5  excellent
      > 0     marginal
      <= 0    unusable
    """
    if len(positive_scores) < min_controls or len(negative_scores) < min_controls:
        return AssayQualityMetrics(
            z_prime=None,
            quality="insufficient",
            positive_mean=0.0,
            positive_std=0.0,
            negative_mean=0.0,
            negative_std=0.0,
            positive_count=len(positive_scores),
            negative_count=len(negative_scores),
        )

    mu_pos = mean(positive_scores)
    mu_neg = mean(negative_scores)
    sigma_pos = stdev(positive_scores) if len(positive_scores) > 1 else 0.0
    sigma_neg = stdev(negative_scores) if len(negative_scores) > 1 else 0.0

    separation = abs(mu_pos - mu_neg)
    z_prime = 0.0 if separation == 0.0 else 1.0 - (3.0 * sigma_pos + 3.0 * sigma_neg) / separation

    if z_prime >= 0.5:
        quality = "excellent"
    elif z_prime > 0.0:
        quality = "marginal"
    else:
        quality = "unusable"

    return AssayQualityMetrics(
        z_prime=z_prime,
        quality=quality,
        positive_mean=mu_pos,
        positive_std=sigma_pos,
        negative_mean=mu_neg,
        negative_std=sigma_neg,
        positive_count=len(positive_scores),
        negative_count=len(negative_scores),
    )

"""Domain-agnostic causal inference service.

Follows the same ports-and-adapters pattern as PredictionService:
estimators are injected via ports, not hardcoded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ehrlich.analysis.domain.causal import CostEffectivenessResult, ThreatToValidity

if TYPE_CHECKING:
    from ehrlich.analysis.domain.causal import CausalEstimate
    from ehrlich.analysis.domain.causal_ports import (
        DiDEstimatorPort,
        PSMEstimatorPort,
        RDDEstimatorPort,
        SyntheticControlPort,
    )


class CausalService:
    """Domain-agnostic causal inference service."""

    def estimate_did(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
        *,
        estimator: DiDEstimatorPort,
    ) -> CausalEstimate:
        return estimator.estimate(
            treatment_pre,
            treatment_post,
            control_pre,
            control_post,
        )

    def estimate_psm(
        self,
        treated_outcomes: list[float],
        control_outcomes: list[float],
        treated_covariates: list[list[float]],
        control_covariates: list[list[float]],
        *,
        estimator: PSMEstimatorPort,
    ) -> CausalEstimate:
        return estimator.estimate(
            treated_outcomes,
            control_outcomes,
            treated_covariates,
            control_covariates,
        )

    def estimate_rdd(
        self,
        running_variable: list[float],
        outcome: list[float],
        cutoff: float,
        *,
        estimator: RDDEstimatorPort,
        bandwidth: float | None = None,
        design: str = "sharp",
    ) -> CausalEstimate:
        return estimator.estimate(
            running_variable,
            outcome,
            cutoff,
            bandwidth,
            design,
        )

    def estimate_synthetic_control(
        self,
        treated_series: list[float],
        donor_matrix: list[list[float]],
        treatment_period: int,
        *,
        estimator: SyntheticControlPort,
    ) -> CausalEstimate:
        return estimator.estimate(
            treated_series,
            donor_matrix,
            treatment_period,
        )

    def assess_threats(
        self,
        method: str,
        sample_sizes: dict[str, int],
        parallel_trends_p: float | None = None,
        effect_size: float | None = None,
    ) -> list[ThreatToValidity]:
        """Knowledge-based threat assessment for any causal method."""
        threats: list[ThreatToValidity] = []
        method_lower = method.lower().replace("-", "_").replace(" ", "_")

        # Small sample threats
        min_n = min(sample_sizes.values()) if sample_sizes else 0
        if min_n < 5:
            threats.append(
                ThreatToValidity(
                    type="small_sample",
                    severity="high",
                    description=(
                        f"Minimum group size is {min_n}. Insufficient for reliable inference."
                    ),
                    mitigation="Increase sample size or use exact/permutation tests.",
                )
            )
        elif min_n < 30:
            threats.append(
                ThreatToValidity(
                    type="small_sample",
                    severity="medium",
                    description=f"Minimum group size is {min_n}. May limit statistical power.",
                    mitigation="Report power analysis and consider non-parametric tests.",
                )
            )

        # Method-specific threats
        is_did = method_lower in ("did", "difference_in_differences")
        if is_did and parallel_trends_p is not None and parallel_trends_p < 0.05:
            threats.append(
                ThreatToValidity(
                    type="parallel_trends_violation",
                    severity="high",
                    description=f"Parallel trends assumption violated (p={parallel_trends_p:.4f}).",
                    mitigation="Use event study or synthetic control method.",
                )
            )

        if method_lower in ("psm", "propensity_score_matching"):
            threats.append(
                ThreatToValidity(
                    type="unobserved_confounders",
                    severity="medium",
                    description="PSM cannot account for unobserved confounders.",
                    mitigation="Combine with sensitivity analysis (Rosenbaum bounds).",
                )
            )

        if method_lower in ("rdd", "regression_discontinuity"):
            threats.append(
                ThreatToValidity(
                    type="manipulation",
                    severity="medium",
                    description="Running variable may be subject to manipulation near cutoff.",
                    mitigation="Test for bunching at the cutoff (McCrary density test).",
                )
            )

        if method_lower in ("synthetic_control", "sc"):
            threats.append(
                ThreatToValidity(
                    type="convex_hull",
                    severity="medium",
                    description="Treated unit must lie in convex hull of donors.",
                    mitigation="Check pre-treatment fit quality (RMSPE).",
                )
            )

        # Effect size plausibility
        if effect_size is not None and abs(effect_size) > 2.0:
            threats.append(
                ThreatToValidity(
                    type="implausible_effect",
                    severity="medium",
                    description=f"Effect size ({effect_size:.2f}) is unusually large.",
                    mitigation="Verify data quality and check for measurement errors.",
                )
            )

        return threats

    @staticmethod
    def compute_cost_effectiveness(
        program_name: str,
        total_cost: float,
        total_effect: float,
        currency: str = "USD",
        effect_unit: str = "units",
        comparison_cost: float | None = None,
        comparison_effect: float | None = None,
    ) -> CostEffectivenessResult:
        """Compute cost-effectiveness ratio and optional ICER."""
        cost_per_unit = total_cost / total_effect if total_effect != 0 else 0.0

        icer: float | None = None
        if comparison_cost is not None and comparison_effect is not None:
            delta_cost = total_cost - comparison_cost
            delta_effect = total_effect - comparison_effect
            if delta_effect != 0:
                icer = delta_cost / delta_effect

        return CostEffectivenessResult(
            program_name=program_name,
            total_cost=round(total_cost, 2),
            total_effect=round(total_effect, 4),
            cost_per_unit=round(cost_per_unit, 2),
            currency=currency,
            effect_unit=effect_unit,
            icer=round(icer, 2) if icer is not None else None,
        )

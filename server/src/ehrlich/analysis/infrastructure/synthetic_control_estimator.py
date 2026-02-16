"""Synthetic Control Method causal estimator.

Pure scipy/numpy implementation -- no new dependencies.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize, stats

from ehrlich.analysis.domain.causal import CausalEstimate, ThreatToValidity
from ehrlich.analysis.domain.causal_ports import SyntheticControlPort
from ehrlich.analysis.domain.evidence_standards import classify_evidence_tier


class SyntheticControlEstimator(SyntheticControlPort):
    """Synthetic control method estimator via constrained optimization."""

    def estimate(
        self,
        treated_series: list[float],
        donor_matrix: list[list[float]],
        treatment_period: int,
    ) -> CausalEstimate:
        y_treated = np.array(treated_series, dtype=np.float64)
        donors = np.array(donor_matrix, dtype=np.float64)

        n_periods = len(y_treated)
        n_donors = len(donors)

        if n_donors < 1 or treatment_period < 2 or treatment_period >= n_periods:
            return CausalEstimate(
                method="synthetic_control",
                effect_size=0.0,
                standard_error=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                n_treatment=n_periods - treatment_period,
                n_control=n_donors,
                covariates=(),
                assumptions=(
                    "No interference between units",
                    "Convex hull condition",
                    "No anticipation effects",
                    "Stable unit composition",
                ),
                threats=(
                    ThreatToValidity(
                        type="insufficient_data",
                        severity="high",
                        description="Insufficient data for synthetic control estimation.",
                        mitigation="Ensure at least 2 pre-treatment periods and 1 donor.",
                    ),
                ),
                evidence_tier="rationale",
            )

        # Ensure donor series match treated length
        donor_pre = np.zeros((n_donors, treatment_period))
        donor_post = np.zeros((n_donors, n_periods - treatment_period))
        for i, d in enumerate(donors):
            d_arr = np.array(d, dtype=np.float64)
            d_len = min(len(d_arr), n_periods)
            pre_len = min(d_len, treatment_period)
            post_len = min(d_len - treatment_period, n_periods - treatment_period)
            donor_pre[i, :pre_len] = d_arr[:pre_len]
            if post_len > 0:
                donor_post[i, :post_len] = d_arr[treatment_period : treatment_period + post_len]

        y_pre = y_treated[:treatment_period]
        y_post = y_treated[treatment_period:]

        # Optimize weights: minimize pre-treatment RMSPE
        # Constraints: weights sum to 1, all >= 0
        def objective(w: np.ndarray) -> float:
            synthetic = donor_pre.T @ w
            return float(np.sum((y_pre - synthetic) ** 2))

        w0 = np.ones(n_donors) / n_donors

        result = optimize.minimize(  # type: ignore[call-overload]
            objective,
            w0,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * n_donors,
            constraints={"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
            options={"maxiter": 500},
        )
        weights = result.x

        # Pre-treatment fit quality
        synthetic_pre = donor_pre.T @ weights
        pre_residuals = y_pre - synthetic_pre
        rmspe = float(np.sqrt(np.mean(pre_residuals**2)))
        sd_treated_pre = float(np.std(y_pre, ddof=1)) if len(y_pre) > 1 else 1.0

        # Post-treatment effect
        synthetic_post = donor_post.T @ weights
        post_gaps = y_post - synthetic_post
        effect = float(np.mean(post_gaps))

        # Standard error from post-treatment gaps
        n_post = len(post_gaps)
        se = float(np.std(post_gaps, ddof=1) / math.sqrt(n_post)) if n_post > 1 else 0.0

        # p-value via t-test on post-treatment gaps
        if se > 0:
            t_stat = effect / se
            df = max(n_post - 1, 1)
            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df)))
        else:
            p_value = 1.0

        ci_lower = effect - 1.96 * se
        ci_upper = effect + 1.96 * se

        threats = self._assess_threats(
            rmspe,
            sd_treated_pre,
            n_donors,
            y_pre,
            synthetic_pre,
            effect,
        )
        evidence_tier = classify_evidence_tier("synthetic_control", list(threats))

        return CausalEstimate(
            method="synthetic_control",
            effect_size=round(effect, 4),
            standard_error=round(se, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            p_value=round(p_value, 6),
            n_treatment=n_post,
            n_control=n_donors,
            covariates=(),
            assumptions=(
                "No interference between units",
                "Convex hull condition",
                "No anticipation effects",
                "Stable unit composition",
            ),
            threats=tuple(threats),
            evidence_tier=evidence_tier,
        )

    @staticmethod
    def _assess_threats(
        rmspe: float,
        sd_treated_pre: float,
        n_donors: int,
        y_pre: np.ndarray,
        synthetic_pre: np.ndarray,
        effect_size: float,
    ) -> list[ThreatToValidity]:
        threats: list[ThreatToValidity] = []

        # 1. Poor pre-treatment fit
        fit_ratio = rmspe / sd_treated_pre if sd_treated_pre > 0 else rmspe
        if fit_ratio > 0.2:
            threats.append(
                ThreatToValidity(
                    type="poor_pretreatment_fit",
                    severity="high" if fit_ratio > 0.5 else "medium",
                    description=(
                        f"Pre-treatment RMSPE is {fit_ratio:.1%} of treated SD. "
                        "Synthetic control may not adequately replicate treated unit."
                    ),
                    mitigation="Add more donor units or covariates to improve fit.",
                )
            )

        # 2. Few donors
        if n_donors < 5:
            threats.append(
                ThreatToValidity(
                    type="few_donors",
                    severity="medium" if n_donors >= 3 else "high",
                    description=(
                        f"Only {n_donors} donor units available. "
                        "Small donor pool limits synthetic control quality."
                    ),
                    mitigation="Expand donor pool or consider alternative methods.",
                )
            )

        # 3. Anticipation effects (check if gap starts before treatment)
        if len(y_pre) >= 4:
            last_gaps = y_pre[-2:] - synthetic_pre[-2:]
            first_gaps = y_pre[:2] - synthetic_pre[:2]
            if float(np.mean(np.abs(last_gaps))) > 2 * float(np.mean(np.abs(first_gaps)) + 1e-10):
                threats.append(
                    ThreatToValidity(
                        type="anticipation_effects",
                        severity="medium",
                        description="Pre-treatment fit deteriorates near treatment date.",
                        mitigation="Test with earlier treatment date placebo.",
                    )
                )

        # 4. Effect size plausibility
        if abs(effect_size) > 2.0:
            threats.append(
                ThreatToValidity(
                    type="implausible_effect",
                    severity="medium",
                    description=f"Effect size ({effect_size:.2f}) is unusually large.",
                    mitigation="Verify data quality and check for measurement errors.",
                )
            )

        return threats

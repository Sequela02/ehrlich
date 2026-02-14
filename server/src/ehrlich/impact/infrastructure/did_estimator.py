"""Difference-in-Differences causal estimator.

Pure scipy/numpy implementation -- no new dependencies.
"""

from __future__ import annotations

import math

from scipy import stats

from ehrlich.impact.domain.entities import CausalEstimate, ThreatToValidity
from ehrlich.impact.domain.evaluation_standards import classify_evidence_tier
from ehrlich.impact.domain.ports import CausalEstimator


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


class DiDEstimator(CausalEstimator):
    """Difference-in-differences estimator with threat assessment."""

    def estimate_did(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
    ) -> CausalEstimate:
        # DiD = (mean_post_T - mean_pre_T) - (mean_post_C - mean_pre_C)
        treatment_diff = _mean(treatment_post) - _mean(treatment_pre)
        control_diff = _mean(control_post) - _mean(control_pre)
        did_estimate = treatment_diff - control_diff

        # Standard error via pooled variance
        n_t = len(treatment_pre) + len(treatment_post)
        n_c = len(control_pre) + len(control_post)

        var_t_pre = _variance(treatment_pre)
        var_t_post = _variance(treatment_post)
        var_c_pre = _variance(control_pre)
        var_c_post = _variance(control_post)

        se_treatment = math.sqrt(
            var_t_pre / max(len(treatment_pre), 1)
            + var_t_post / max(len(treatment_post), 1)
        )
        se_control = math.sqrt(
            var_c_pre / max(len(control_pre), 1)
            + var_c_post / max(len(control_post), 1)
        )
        se_did = math.sqrt(se_treatment**2 + se_control**2)

        # t-test for significance (treatment post vs control post, adjusted)
        if se_did > 0:
            t_stat = did_estimate / se_did
            df = n_t + n_c - 4
            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=max(df, 1))))
        else:
            p_value = 1.0

        # Cohen's d effect size
        pooled_sd = math.sqrt(
            (var_t_post * max(len(treatment_post) - 1, 0)
             + var_c_post * max(len(control_post) - 1, 0))
            / max(len(treatment_post) + len(control_post) - 2, 1)
        )
        cohens_d = did_estimate / pooled_sd if pooled_sd > 0 else 0.0

        # 95% confidence interval
        ci_margin = 1.96 * se_did
        ci_lower = did_estimate - ci_margin
        ci_upper = did_estimate + ci_margin

        # Automated threat assessment
        threats = self._assess_threats(
            treatment_pre, treatment_post,
            control_pre, control_post,
            p_value, cohens_d,
        )

        evidence_tier = classify_evidence_tier("did", list(threats))

        return CausalEstimate(
            method="difference_in_differences",
            effect_size=round(did_estimate, 4),
            standard_error=round(se_did, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            p_value=round(p_value, 6),
            n_treatment=n_t,
            n_control=n_c,
            covariates=(),
            assumptions=(
                "Parallel trends",
                "No spillover (SUTVA)",
                "Common support",
                "No anticipation effects",
            ),
            threats=threats,
            evidence_tier=evidence_tier,
        )

    def _assess_threats(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
        p_value: float,
        effect_size: float,
    ) -> tuple[ThreatToValidity, ...]:
        threats: list[ThreatToValidity] = []

        # 1. Parallel trends test: compare pre-treatment slopes
        pt_p = self._parallel_trends_p(treatment_pre, control_pre)
        if pt_p < 0.05:
            threats.append(ThreatToValidity(
                type="parallel_trends_violation",
                severity="high",
                description=(
                    f"Pre-treatment trends differ significantly (p={pt_p:.4f}). "
                    "DiD assumption of parallel trends may be violated."
                ),
                mitigation="Consider event study design or synthetic control method.",
            ))
        elif pt_p < 0.10:
            threats.append(ThreatToValidity(
                type="parallel_trends_weak",
                severity="medium",
                description=(
                    f"Pre-treatment trends show marginal difference (p={pt_p:.4f}). "
                    "Parallel trends assumption is weakly supported."
                ),
                mitigation="Report sensitivity analysis with alternative control groups.",
            ))

        # 2. Small sample size
        min_n = min(
            len(treatment_pre), len(treatment_post),
            len(control_pre), len(control_post),
        )
        if min_n < 5:
            threats.append(ThreatToValidity(
                type="small_sample",
                severity="high",
                description=(
                    f"Minimum group size is {min_n}. "
                    "Small samples reduce statistical power."
                ),
                mitigation="Increase sample size or use bootstrapped CIs.",
            ))
        elif min_n < 10:
            threats.append(ThreatToValidity(
                type="small_sample",
                severity="medium",
                description=(
                    f"Minimum group size is {min_n}. "
                    "Moderate sample may limit generalizability."
                ),
                mitigation="Consider non-parametric alternatives.",
            ))

        # 3. Effect size plausibility
        if abs(effect_size) > 2.0:
            threats.append(ThreatToValidity(
                type="implausible_effect",
                severity="medium",
                description=(
                    f"Effect size of {effect_size:.2f} is unusually large "
                    "for social program evaluation."
                ),
                mitigation="Verify data quality and check for measurement errors.",
            ))

        # 4. Borderline significance
        if 0.01 < p_value < 0.05:
            threats.append(ThreatToValidity(
                type="borderline_significance",
                severity="low",
                description=(
                    "Result is statistically significant "
                    f"but borderline (p={p_value:.4f})."
                ),
                mitigation="Pre-register hypothesis and consider multiple testing correction.",
            ))

        return tuple(threats)

    @staticmethod
    def _parallel_trends_p(
        treatment_pre: list[float],
        control_pre: list[float],
    ) -> float:
        """Test parallel trends by comparing pre-treatment group distributions."""
        if len(treatment_pre) < 2 or len(control_pre) < 2:
            return 1.0

        # Compare trends using Mann-Whitney U test on pre-treatment values
        _, p_value = stats.mannwhitneyu(
            treatment_pre, control_pre, alternative="two-sided",
        )
        return float(p_value)

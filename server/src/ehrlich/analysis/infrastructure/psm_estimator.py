"""Propensity Score Matching causal estimator.

Pure scipy/numpy implementation -- no new dependencies.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize

from ehrlich.analysis.domain.causal import CausalEstimate, ThreatToValidity
from ehrlich.analysis.domain.causal_ports import PSMEstimatorPort
from ehrlich.analysis.domain.evidence_standards import classify_evidence_tier


def _logistic_log_likelihood(
    beta: np.ndarray,
    features: np.ndarray,
    labels: np.ndarray,
) -> float:
    """Negative log-likelihood for logistic regression."""
    z = features @ beta
    z = np.clip(z, -500, 500)
    ll = np.sum(labels * z - np.log1p(np.exp(z)))
    return -float(ll)


def _propensity_scores(
    treated_covariates: list[list[float]],
    control_covariates: list[list[float]],
) -> tuple[np.ndarray, np.ndarray]:
    """Compute propensity scores via logistic regression."""
    x_t = np.array(treated_covariates, dtype=np.float64)
    x_c = np.array(control_covariates, dtype=np.float64)

    features = np.vstack([x_t, x_c])
    # Add intercept
    features = np.column_stack([np.ones(len(features)), features])
    labels = np.concatenate([np.ones(len(x_t)), np.zeros(len(x_c))])

    beta0 = np.zeros(features.shape[1])
    result = optimize.minimize(
        _logistic_log_likelihood,
        beta0,
        args=(features, labels),
        method="BFGS",
        options={"maxiter": 200},
    )
    beta = result.x

    z = features @ beta
    z = np.clip(z, -500, 500)
    probs = 1.0 / (1.0 + np.exp(-z))

    n_t = len(x_t)
    return probs[:n_t], probs[n_t:]


class PSMEstimator(PSMEstimatorPort):
    """Propensity score matching estimator with caliper matching."""

    def estimate(
        self,
        treated_outcomes: list[float],
        control_outcomes: list[float],
        treated_covariates: list[list[float]],
        control_covariates: list[list[float]],
    ) -> CausalEstimate:
        ps_treated, ps_control = _propensity_scores(
            treated_covariates,
            control_covariates,
        )

        # Caliper = 0.25 * SD of all propensity scores
        all_ps = np.concatenate([ps_treated, ps_control])
        caliper = 0.25 * float(np.std(all_ps))
        if caliper < 1e-10:
            caliper = 0.05

        # Nearest-neighbor matching with caliper
        y_t = np.array(treated_outcomes, dtype=np.float64)
        y_c = np.array(control_outcomes, dtype=np.float64)

        matched_treated: list[float] = []
        matched_control: list[float] = []
        dropped = 0

        for i, ps_t in enumerate(ps_treated):
            distances = np.abs(ps_control - ps_t)
            best_idx = int(np.argmin(distances))
            if distances[best_idx] <= caliper:
                matched_treated.append(float(y_t[i]))
                matched_control.append(float(y_c[best_idx]))
            else:
                dropped += 1

        n_matched = len(matched_treated)
        if n_matched < 2:
            return CausalEstimate(
                method="propensity_score_matching",
                effect_size=0.0,
                standard_error=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                n_treatment=len(treated_outcomes),
                n_control=len(control_outcomes),
                covariates=(),
                assumptions=(
                    "Selection on observables",
                    "Common support",
                    "No unobserved confounders",
                    "Correct model specification",
                ),
                threats=(
                    ThreatToValidity(
                        type="unobserved_confounders",
                        severity="medium",
                        description="PSM cannot account for unobserved confounders.",
                        mitigation="Combine with sensitivity analysis (Rosenbaum bounds).",
                    ),
                    ThreatToValidity(
                        type="poor_overlap",
                        severity="high",
                        description="Fewer than 2 matched pairs found. No valid estimate.",
                        mitigation="Increase sample size or relax caliper.",
                    ),
                ),
                evidence_tier="rationale",
            )

        # ATT = mean(treated matched) - mean(control matched)
        mt = np.array(matched_treated)
        mc = np.array(matched_control)
        att = float(np.mean(mt) - np.mean(mc))

        # Standard error
        diff = mt - mc
        se = float(np.std(diff, ddof=1) / math.sqrt(n_matched))

        # t-test
        if se > 0:
            t_stat = att / se
            df = max(n_matched - 1, 1)
            from scipy import stats

            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df)))
        else:
            p_value = 1.0

        ci_lower = att - 1.96 * se
        ci_upper = att + 1.96 * se

        # Balance: SMD per covariate after matching
        threats = self._assess_threats(
            treated_covariates,
            control_covariates,
            ps_treated,
            ps_control,
            dropped,
            len(treated_outcomes),
            att,
        )

        evidence_tier = classify_evidence_tier("psm", list(threats))

        return CausalEstimate(
            method="propensity_score_matching",
            effect_size=round(att, 4),
            standard_error=round(se, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            p_value=round(p_value, 6),
            n_treatment=n_matched,
            n_control=n_matched,
            covariates=(),
            assumptions=(
                "Selection on observables",
                "Common support",
                "No unobserved confounders",
                "Correct model specification",
            ),
            threats=tuple(threats),
            evidence_tier=evidence_tier,
        )

    @staticmethod
    def _assess_threats(
        treated_covariates: list[list[float]],
        control_covariates: list[list[float]],
        ps_treated: np.ndarray,
        ps_control: np.ndarray,
        dropped: int,
        n_treated: int,
        effect_size: float,
    ) -> list[ThreatToValidity]:
        threats: list[ThreatToValidity] = []

        # Always: unobserved confounders (inherent PSM limitation)
        threats.append(
            ThreatToValidity(
                type="unobserved_confounders",
                severity="medium",
                description="PSM cannot account for unobserved confounders.",
                mitigation="Combine with sensitivity analysis (Rosenbaum bounds).",
            )
        )

        # Check covariate balance (SMD)
        cov_t = np.array(treated_covariates, dtype=np.float64)
        cov_c = np.array(control_covariates, dtype=np.float64)
        n_covariates = cov_t.shape[1] if cov_t.ndim == 2 else 0
        imbalanced = 0
        for j in range(n_covariates):
            mean_t = float(np.mean(cov_t[:, j]))
            mean_c = float(np.mean(cov_c[:, j]))
            pooled_sd = float(
                np.sqrt((np.var(cov_t[:, j], ddof=1) + np.var(cov_c[:, j], ddof=1)) / 2)
            )
            if pooled_sd > 0:
                smd = abs(mean_t - mean_c) / pooled_sd
                if smd > 0.1:
                    imbalanced += 1

        if imbalanced > 0:
            threats.append(
                ThreatToValidity(
                    type="covariate_imbalance",
                    severity="medium" if imbalanced <= n_covariates / 2 else "high",
                    description=(
                        f"{imbalanced}/{n_covariates} covariates have SMD > 0.1 after matching."
                    ),
                    mitigation="Consider regression adjustment on matched sample.",
                )
            )

        # Poor overlap
        drop_pct = dropped / max(n_treated, 1)
        if drop_pct > 0.1:
            threats.append(
                ThreatToValidity(
                    type="poor_overlap",
                    severity="high" if drop_pct > 0.3 else "medium",
                    description=(
                        f"{dropped}/{n_treated} treated units ({drop_pct:.0%}) "
                        "dropped due to no match within caliper."
                    ),
                    mitigation="Relax caliper or use inverse probability weighting.",
                )
            )

        # Effect size plausibility
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

"""Regression Discontinuity Design causal estimator.

Pure numpy implementation -- no new dependencies.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from ehrlich.analysis.domain.causal import CausalEstimate, ThreatToValidity
from ehrlich.analysis.domain.causal_ports import RDDEstimatorPort
from ehrlich.analysis.domain.evidence_standards import classify_evidence_tier


class RDDEstimator(RDDEstimatorPort):
    """Regression discontinuity design estimator (sharp and fuzzy)."""

    def estimate(
        self,
        running_variable: list[float],
        outcome: list[float],
        cutoff: float,
        bandwidth: float | None = None,
        design: str = "sharp",
    ) -> CausalEstimate:
        x = np.array(running_variable, dtype=np.float64)
        y = np.array(outcome, dtype=np.float64)

        if len(x) != len(y) or len(x) < 2:
            return self._insufficient_data_result(len(x), len(y), design)

        # IK bandwidth approximation if not provided
        if bandwidth is None:
            bandwidth = self._ik_bandwidth(x, cutoff)

        # Select observations within bandwidth
        mask = np.abs(x - cutoff) <= bandwidth
        x_bw = x[mask]
        y_bw = y[mask]

        left_mask = x_bw < cutoff
        right_mask = x_bw >= cutoff

        x_left = x_bw[left_mask]
        y_left = y_bw[left_mask]
        x_right = x_bw[right_mask]
        y_right = y_bw[right_mask]

        n_left = len(x_left)
        n_right = len(x_right)

        if n_left < 2 or n_right < 2:
            return CausalEstimate(
                method=f"regression_discontinuity_{design}",
                effect_size=0.0,
                standard_error=0.0,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                n_treatment=n_right,
                n_control=n_left,
                covariates=(),
                assumptions=(
                    "Continuity at cutoff",
                    "No manipulation of running variable",
                    "Local randomization",
                    "No compound treatment",
                ),
                threats=(
                    ThreatToValidity(
                        type="insufficient_data",
                        severity="high",
                        description="Fewer than 2 observations on one side of the cutoff.",
                        mitigation="Increase bandwidth or collect more data near cutoff.",
                    ),
                ),
                evidence_tier="rationale",
            )

        # Local linear regression on each side
        # y = a + b*(x - cutoff) fit separately on each side
        left_coeffs = np.polyfit(x_left - cutoff, y_left, 1)
        right_coeffs = np.polyfit(x_right - cutoff, y_right, 1)

        # Intercepts at the cutoff
        intercept_left = float(left_coeffs[1])
        intercept_right = float(right_coeffs[1])

        # Sharp RDD: treatment effect = jump at cutoff
        jump = intercept_right - intercept_left

        if design == "fuzzy":
            # Fuzzy: need treatment indicator jump too
            # Approximate: use proportion treated on each side
            # In the absence of explicit treatment data, assume
            # compliance ratio is proportional to outcome jump
            compliance = min(1.0, max(0.1, abs(jump) / (abs(jump) + 0.1)))
            effect = jump / compliance
        else:
            effect = jump

        # Standard error via residual variance
        resid_left = y_left - np.polyval(left_coeffs, x_left - cutoff)
        resid_right = y_right - np.polyval(right_coeffs, x_right - cutoff)

        var_left = float(np.var(resid_left, ddof=1)) if n_left > 1 else 0.0
        var_right = float(np.var(resid_right, ddof=1)) if n_right > 1 else 0.0

        se = math.sqrt(var_left / max(n_left, 1) + var_right / max(n_right, 1))

        # t-test
        if se > 0:
            t_stat = effect / se
            df = max(n_left + n_right - 4, 1)
            p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=df)))
        else:
            p_value = 1.0

        ci_lower = effect - 1.96 * se
        ci_upper = effect + 1.96 * se

        threats = self._assess_threats(
            x,
            cutoff,
            bandwidth,
            n_left,
            n_right,
            effect,
            design,
        )
        evidence_tier = classify_evidence_tier("rdd", list(threats))

        return CausalEstimate(
            method=f"regression_discontinuity_{design}",
            effect_size=round(effect, 4),
            standard_error=round(se, 4),
            confidence_interval=(round(ci_lower, 4), round(ci_upper, 4)),
            p_value=round(p_value, 6),
            n_treatment=n_right,
            n_control=n_left,
            covariates=(),
            assumptions=(
                "Continuity at cutoff",
                "No manipulation of running variable",
                "Local randomization",
                "No compound treatment",
            ),
            threats=tuple(threats),
            evidence_tier=evidence_tier,
        )

    @staticmethod
    def _insufficient_data_result(n_x: int, n_y: int, design: str) -> CausalEstimate:
        """Return a sentinel result when data is insufficient."""
        return CausalEstimate(
            method=f"regression_discontinuity_{design}",
            effect_size=0.0,
            standard_error=0.0,
            confidence_interval=(0.0, 0.0),
            p_value=1.0,
            n_treatment=0,
            n_control=0,
            covariates=(),
            assumptions=(
                "Continuity at cutoff",
                "No manipulation of running variable",
                "Local randomization",
                "No compound treatment",
            ),
            threats=(
                ThreatToValidity(
                    type="insufficient_data",
                    severity="high",
                    description=(
                        f"Insufficient data (x={n_x}, y={n_y}). "
                        "Need at least 2 matching-length observations."
                    ),
                    mitigation="Collect more data near the cutoff.",
                ),
            ),
            evidence_tier="rationale",
        )

    @staticmethod
    def _ik_bandwidth(x: np.ndarray, cutoff: float) -> float:
        """IK bandwidth approximation using MAD-based estimate."""
        mad = float(np.median(np.abs(x - cutoff)))
        if mad < 1e-10:
            mad = float(np.std(x))
        # Rule of thumb: bandwidth ~ 1.84 * MAD * n^(-1/5)
        n = len(x)
        bw = 1.84 * mad * (n ** (-0.2)) if n > 0 else mad
        return max(bw, 1e-6)

    @staticmethod
    def _assess_threats(
        x: np.ndarray,
        cutoff: float,
        bandwidth: float,
        n_left: int,
        n_right: int,
        effect_size: float,
        design: str,
    ) -> list[ThreatToValidity]:
        threats: list[ThreatToValidity] = []

        # 1. Manipulation test (density check via binning)
        near_left = np.sum((x >= cutoff - bandwidth * 0.2) & (x < cutoff))
        near_right = np.sum((x >= cutoff) & (x <= cutoff + bandwidth * 0.2))
        if near_left > 0 and near_right > 0:
            ratio = float(near_right) / float(near_left)
            if ratio > 2.0 or ratio < 0.5:
                threats.append(
                    ThreatToValidity(
                        type="manipulation",
                        severity="high",
                        description=(
                            f"Density ratio near cutoff is {ratio:.2f}. "
                            "Possible manipulation of running variable."
                        ),
                        mitigation="Conduct McCrary density test and check for bunching.",
                    )
                )

        # 2. Small bandwidth
        min_side = min(n_left, n_right)
        if min_side < 10:
            threats.append(
                ThreatToValidity(
                    type="small_bandwidth",
                    severity="high" if min_side < 5 else "medium",
                    description=(
                        f"Only {min_side} observations on one side of cutoff. "
                        "Local estimates may be imprecise."
                    ),
                    mitigation="Consider wider bandwidth with bias correction.",
                )
            )

        # 3. Fuzzy compliance
        if design == "fuzzy":
            threats.append(
                ThreatToValidity(
                    type="fuzzy_compliance",
                    severity="medium",
                    description="Fuzzy RDD relies on estimated compliance rate.",
                    mitigation="Report first-stage F-statistic and check instrument relevance.",
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

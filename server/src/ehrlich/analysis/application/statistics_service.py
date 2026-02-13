from __future__ import annotations

import math

import numpy as np
from scipy import stats

from ehrlich.analysis.domain.statistics import StatisticalResult


class StatisticsService:
    """Domain-agnostic statistical hypothesis testing."""

    def run_test(
        self,
        group_a: list[float],
        group_b: list[float],
        test: str = "auto",
        alpha: float = 0.05,
    ) -> StatisticalResult:
        """Compare two groups of continuous data with the appropriate test."""
        a = np.array(group_a, dtype=np.float64)
        b = np.array(group_b, dtype=np.float64)

        if len(a) < 2 or len(b) < 2:
            msg = "Each group must have at least 2 observations"
            raise ValueError(msg)

        test_name = self._select_continuous_test(a, b) if test == "auto" else test

        if test_name in ("t_test", "welch_t"):
            equal_var = test_name == "t_test"
            t_result = stats.ttest_ind(a, b, equal_var=equal_var)
            stat, p = float(t_result.statistic), float(t_result.pvalue)
        else:  # mann_whitney
            u_result = stats.mannwhitneyu(a, b, alternative="two-sided")
            stat, p = float(u_result.statistic), float(u_result.pvalue)

        effect, ci_lo, ci_hi = self._cohens_d_with_ci(a, b)

        sig = p < alpha
        interp = (
            f"Significant difference (p={p:.4f}, d={effect:.2f})"
            if sig
            else f"No significant difference (p={p:.4f}, d={effect:.2f})"
        )

        return StatisticalResult(
            test_name=test_name,
            test_statistic=stat,
            p_value=p,
            effect_size=effect,
            effect_size_type="cohens_d",
            ci_lower=ci_lo,
            ci_upper=ci_hi,
            sample_size_a=len(a),
            sample_size_b=len(b),
            significant=sig,
            alpha=alpha,
            interpretation=interp,
        )

    def run_categorical_test(
        self,
        table: list[list[int]],
        test: str = "auto",
        alpha: float = 0.05,
    ) -> StatisticalResult:
        """Test association in a contingency table."""
        arr = np.array(table, dtype=np.int64)
        if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 2:
            msg = "Table must be at least 2x2"
            raise ValueError(msg)

        is_2x2 = arr.shape == (2, 2)
        test_name = self._select_categorical_test(arr, test)

        if test_name == "fisher_exact":
            fisher = stats.fisher_exact(arr)
            odds = float(fisher.statistic)
            p = float(fisher.pvalue)
            stat = odds
            effect = odds
            effect_type = "odds_ratio"
        else:
            chi2_result = stats.chi2_contingency(arr)
            stat, p = float(chi2_result.statistic), float(chi2_result.pvalue)
            if is_2x2:
                a, b, c, d = arr.ravel()
                effect = float((a * d) / (b * c)) if (b * c) > 0 else float("inf")
                effect_type = "odds_ratio"
            else:
                n = arr.sum()
                k = min(arr.shape) - 1
                effect = float(math.sqrt(stat / (n * k))) if n * k > 0 else 0.0
                effect_type = "cramers_v"

        n_a = int(arr[0].sum())
        n_b = int(arr[1].sum())
        sig = p < alpha
        interp = (
            f"Significant association (p={p:.4f}, {effect_type}={effect:.2f})"
            if sig
            else f"No significant association (p={p:.4f}, {effect_type}={effect:.2f})"
        )

        return StatisticalResult(
            test_name=test_name,
            test_statistic=stat,
            p_value=p,
            effect_size=effect,
            effect_size_type=effect_type,
            ci_lower=0.0,
            ci_upper=0.0,
            sample_size_a=n_a,
            sample_size_b=n_b,
            significant=sig,
            alpha=alpha,
            interpretation=interp,
        )

    @staticmethod
    def _select_continuous_test(a: np.ndarray, b: np.ndarray) -> str:
        """Auto-select: normality check -> variance check -> test."""
        normal_a = _is_normal(a)
        normal_b = _is_normal(b)
        if not (normal_a and normal_b):
            return "mann_whitney"
        _, p_levene = stats.levene(a, b)
        return "t_test" if p_levene >= 0.05 else "welch_t"

    @staticmethod
    def _select_categorical_test(arr: np.ndarray, test: str) -> str:
        if test != "auto":
            return test
        is_2x2 = arr.shape == (2, 2)
        if is_2x2 and arr.min() < 5:
            return "fisher_exact"
        return "chi_squared"

    @staticmethod
    def _cohens_d_with_ci(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
        """Cohen's d with analytic 95% CI (Hedges & Olkin)."""
        na, nb = len(a), len(b)
        pooled_std = float(
            math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
        )
        d = float((a.mean() - b.mean()) / pooled_std) if pooled_std > 0 else 0.0
        se = math.sqrt((na + nb) / (na * nb) + d**2 / (2 * (na + nb)))
        ci_lo = d - 1.96 * se
        ci_hi = d + 1.96 * se
        return d, ci_lo, ci_hi


def _is_normal(x: np.ndarray) -> bool:
    """Check normality: Shapiro-Wilk for n <= 5000, D'Agostino for larger."""
    if len(x) < 8:
        return False
    p = float(stats.shapiro(x).pvalue) if len(x) <= 5000 else float(stats.normaltest(x).pvalue)
    return p >= 0.05

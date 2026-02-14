from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from ehrlich.analysis.application.statistics_service import StatisticsService

if TYPE_CHECKING:
    from ehrlich.impact.domain.entities import (
        Benchmark,
        CausalEstimate,
        EconomicSeries,
        HealthIndicator,
        ThreatToValidity,
    )
    from ehrlich.impact.domain.ports import CausalEstimator
    from ehrlich.impact.domain.repository import (
        DevelopmentDataRepository,
        EconomicDataRepository,
        HealthDataRepository,
    )


class ImpactService:
    def __init__(
        self,
        economic: EconomicDataRepository | None = None,
        health: HealthDataRepository | None = None,
        development: DevelopmentDataRepository | None = None,
        causal_estimator: CausalEstimator | None = None,
    ) -> None:
        self._economic = economic
        self._health = health
        self._development = development
        self._causal = causal_estimator
        self._stats = StatisticsService()

    async def search_economic_data(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._economic:
            return []
        return await self._economic.search_series(query, limit)

    async def get_economic_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None:
        if not self._economic:
            return None
        return await self._economic.get_series(series_id, start, end)

    async def search_health_data(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[HealthIndicator]:
        if not self._health:
            return []
        return await self._health.search_indicators(indicator, country, year_start, year_end, limit)

    async def search_development_data(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[Benchmark]:
        if not self._development:
            return []
        return await self._development.search_indicators(
            indicator, country, year_start, year_end, limit
        )

    async def fetch_benchmark(
        self,
        indicator: str,
        source: str,
        country: str | None = None,
        period: str | None = None,
    ) -> list[dict[str, object]]:
        """Fetch benchmark from the appropriate source."""
        year_start = int(period.split("-")[0]) if period and "-" in period else None
        year_end = int(period.split("-")[1]) if period and "-" in period else None

        if source in ("fred", "economic"):
            series = await self.search_economic_data(indicator, limit=5)
            return [
                {
                    "source": "FRED",
                    "series_id": s.series_id,
                    "title": s.title,
                    "unit": s.unit,
                    "frequency": s.frequency,
                }
                for s in series
            ]

        if source in ("who", "health"):
            health_results = await self.search_health_data(
                indicator, country, year_start, year_end, limit=10
            )
            return [asdict(r) for r in health_results]

        if source in ("world_bank", "development"):
            dev_results = await self.search_development_data(
                indicator, country, year_start, year_end, limit=10
            )
            return [asdict(r) for r in dev_results]

        return []

    def estimate_did(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
    ) -> CausalEstimate:
        """Estimate causal effect using difference-in-differences."""
        if not self._causal:
            msg = "No causal estimator configured"
            raise RuntimeError(msg)
        return self._causal.estimate_did(
            treatment_pre, treatment_post, control_pre, control_post,
        )

    def assess_threats(
        self,
        method: str,
        sample_sizes: dict[str, int],
        parallel_trends_p: float | None = None,
        effect_size: float | None = None,
    ) -> list[ThreatToValidity]:
        """Knowledge-based threat assessment for any causal method."""
        from ehrlich.impact.domain.entities import ThreatToValidity

        threats: list[ThreatToValidity] = []
        method_lower = method.lower().replace("-", "_").replace(" ", "_")

        # Small sample threats
        min_n = min(sample_sizes.values()) if sample_sizes else 0
        if min_n < 5:
            threats.append(ThreatToValidity(
                type="small_sample",
                severity="high",
                description=f"Minimum group size is {min_n}. Insufficient for reliable inference.",
                mitigation="Increase sample size or use exact/permutation tests.",
            ))
        elif min_n < 30:
            threats.append(ThreatToValidity(
                type="small_sample",
                severity="medium",
                description=f"Minimum group size is {min_n}. May limit statistical power.",
                mitigation="Report power analysis and consider non-parametric tests.",
            ))

        # Method-specific threats
        is_did = method_lower in ("did", "difference_in_differences")
        if is_did and parallel_trends_p is not None and parallel_trends_p < 0.05:
                threats.append(ThreatToValidity(
                    type="parallel_trends_violation",
                    severity="high",
                    description=f"Parallel trends assumption violated (p={parallel_trends_p:.4f}).",
                    mitigation="Use event study or synthetic control method.",
                ))

        if method_lower in ("psm", "propensity_score_matching"):
            threats.append(ThreatToValidity(
                type="unobserved_confounders",
                severity="medium",
                description="PSM cannot account for unobserved confounders.",
                mitigation="Combine with sensitivity analysis (Rosenbaum bounds).",
            ))

        if method_lower in ("rdd", "regression_discontinuity"):
            threats.append(ThreatToValidity(
                type="manipulation",
                severity="medium",
                description="Running variable may be subject to manipulation near cutoff.",
                mitigation="Test for bunching at the cutoff (McCrary density test).",
            ))

        # Effect size plausibility
        if effect_size is not None and abs(effect_size) > 2.0:
            threats.append(ThreatToValidity(
                type="implausible_effect",
                severity="medium",
                description=f"Effect size ({effect_size:.2f}) is unusually large.",
                mitigation="Verify data quality and check for measurement errors.",
            ))

        return threats

    def compare_programs(
        self,
        programs: list[dict[str, object]],
        metric: str,
        alternative: str = "two-sided",
    ) -> dict[str, object]:
        """Compare programs on a metric with statistical testing."""
        values_by_group: dict[str, list[float]] = {}
        for prog in programs:
            name = str(prog.get("name", "unknown"))
            raw_values = prog.get("values", [])
            if isinstance(raw_values, list):
                values_by_group[name] = [float(v) for v in raw_values]

        group_names = list(values_by_group.keys())
        groups = list(values_by_group.values())

        result: dict[str, object] = {
            "metric": metric,
            "groups": {
                name: {
                    "n": len(vals),
                    "mean": round(sum(vals) / len(vals), 4) if vals else 0.0,
                    "min": round(min(vals), 4) if vals else 0.0,
                    "max": round(max(vals), 4) if vals else 0.0,
                }
                for name, vals in values_by_group.items()
            },
        }

        if len(groups) == 2 and all(len(g) >= 2 for g in groups):
            stat_result = self._stats.run_test(groups[0], groups[1])
            result["statistical_test"] = {
                "test_name": stat_result.test_name,
                "test_statistic": stat_result.test_statistic,
                "p_value": stat_result.p_value,
                "effect_size": stat_result.effect_size,
                "significant": stat_result.significant,
                "interpretation": stat_result.interpretation,
            }
            result["comparison"] = f"{group_names[0]} vs {group_names[1]}"

        return result

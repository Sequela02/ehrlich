from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from ehrlich.analysis.application.statistics_service import StatisticsService
from ehrlich.impact.domain.evaluation_standards import CONEVAL_MIR_LEVELS, CREMAA_CRITERIA

if TYPE_CHECKING:
    from ehrlich.impact.domain.entities import (
        Benchmark,
        DatasetMetadata,
        EconomicSeries,
        EducationRecord,
        HealthIndicator,
        HousingData,
        SpendingRecord,
    )
    from ehrlich.impact.domain.repository import (
        DevelopmentDataRepository,
        EconomicDataRepository,
        EducationDataRepository,
        HealthDataRepository,
        HousingDataRepository,
        OpenDataRepository,
        SpendingDataRepository,
    )


class ImpactService:
    def __init__(
        self,
        economic: EconomicDataRepository | None = None,
        health: HealthDataRepository | None = None,
        development: DevelopmentDataRepository | None = None,
        spending: SpendingDataRepository | None = None,
        education: EducationDataRepository | None = None,
        housing: HousingDataRepository | None = None,
        open_data: OpenDataRepository | None = None,
        bls: EconomicDataRepository | None = None,
        census: DevelopmentDataRepository | None = None,
        cdc: HealthDataRepository | None = None,
        inegi: EconomicDataRepository | None = None,
        banxico: EconomicDataRepository | None = None,
        datosgob: OpenDataRepository | None = None,
    ) -> None:
        self._economic = economic
        self._health = health
        self._development = development
        self._spending = spending
        self._education = education
        self._housing = housing
        self._open_data = open_data
        self._bls = bls
        self._census = census
        self._cdc = cdc
        self._inegi = inegi
        self._banxico = banxico
        self._datosgob = datosgob
        self._stats = StatisticsService()

    async def search_economic_data(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._economic:
            return []
        return await self._economic.search_series(query, limit)

    async def search_bls_data(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._bls:
            return []
        return await self._bls.search_series(query, limit)

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

    async def search_cdc_data(
        self,
        indicator: str,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[HealthIndicator]:
        if not self._cdc:
            return []
        return await self._cdc.search_indicators(indicator, "US", year_start, year_end, limit)

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

    async def search_census_data(
        self,
        indicator: str,
        state: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[Benchmark]:
        if not self._census:
            return []
        return await self._census.search_indicators(indicator, state, year_start, year_end, limit)

    async def search_spending_data(
        self,
        query: str,
        agency: str | None = None,
        year: int | None = None,
        limit: int = 10,
    ) -> list[SpendingRecord]:
        if not self._spending:
            return []
        return await self._spending.search_awards(query, agency, year, limit)

    async def search_education_data(
        self,
        query: str,
        state: str | None = None,
        limit: int = 10,
    ) -> list[EducationRecord]:
        if not self._education:
            return []
        return await self._education.search_schools(query, state, limit)

    async def search_housing_data(
        self,
        state: str,
        county: str | None = None,
        year: int | None = None,
    ) -> list[HousingData]:
        if not self._housing:
            return []
        return await self._housing.search_housing_data(state, county, year)

    async def search_open_data(
        self,
        query: str,
        organization: str | None = None,
        limit: int = 10,
    ) -> list[DatasetMetadata]:
        if not self._open_data:
            return []
        return await self._open_data.search_datasets(query, organization, limit)

    async def search_inegi_data(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._inegi:
            return []
        return await self._inegi.search_series(query, limit)

    async def search_banxico_data(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._banxico:
            return []
        return await self._banxico.search_series(query, limit)

    async def search_mexican_open_data(
        self,
        query: str,
        organization: str | None = None,
        limit: int = 10,
    ) -> list[DatasetMetadata]:
        if not self._datosgob:
            return []
        return await self._datosgob.search_datasets(query, organization, limit)

    def analyze_program_indicators(
        self, indicator_name: str, level: str
    ) -> dict[str, object]:
        """Validate an MIR indicator against CREMAA criteria."""
        level_clean = level.lower().strip()
        level_description = CONEVAL_MIR_LEVELS.get(
            level_clean, f"Unknown MIR level: {level_clean}"
        )
        criteria_results: dict[str, dict[str, str]] = {
            criterion: {
                "description": description,
                "status": "requires_review",
                "guidance": f"Evaluate '{indicator_name}' for: {description}",
            }
            for criterion, description in CREMAA_CRITERIA.items()
        }
        return {
            "indicator_name": indicator_name,
            "mir_level": level_clean,
            "mir_level_description": level_description,
            "cremaa_criteria": criteria_results,
            "total_criteria": len(CREMAA_CRITERIA),
        }

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

        if source == "bls":
            series = await self.search_bls_data(indicator, limit=5)
            return [
                {
                    "source": "BLS",
                    "series_id": s.series_id,
                    "title": s.title,
                    "unit": s.unit,
                    "frequency": s.frequency,
                }
                for s in series
            ]

        if source == "census":
            benchmarks = await self.search_census_data(
                indicator, country, year_start, year_end, limit=10
            )
            return [asdict(b) for b in benchmarks]

        if source in ("who", "health"):
            health_results = await self.search_health_data(
                indicator, country, year_start, year_end, limit=10
            )
            return [asdict(r) for r in health_results]

        if source == "cdc":
            cdc_results = await self.search_cdc_data(indicator, year_start, year_end, limit=10)
            return [asdict(r) for r in cdc_results]

        if source in ("world_bank", "development"):
            dev_results = await self.search_development_data(
                indicator, country, year_start, year_end, limit=10
            )
            return [asdict(r) for r in dev_results]

        return []

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

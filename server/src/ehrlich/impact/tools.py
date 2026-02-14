"""Impact Evaluation tools for the investigation engine.

3 tools for social program data retrieval: economic indicator
search, benchmark fetching, and cross-program comparison.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ehrlich.impact.application.impact_service import ImpactService
from ehrlich.impact.infrastructure.fred_client import FREDClient
from ehrlich.impact.infrastructure.who_client import WHOClient
from ehrlich.impact.infrastructure.worldbank_client import WorldBankClient

_worldbank = WorldBankClient()
_who = WHOClient()
_fred = FREDClient()
_service = ImpactService(
    economic=_fred,
    health=_who,
    development=_worldbank,
)


async def search_economic_indicators(
    query: str,
    source: str = "fred",
    country: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    limit: int = 10,
) -> str:
    """Search FRED, World Bank, or WHO for economic/development/health indicators.

    Queries the specified data source for time series data relevant to
    impact evaluation. Returns series metadata and values for analysis.

    Args:
        query: Search query or indicator code
            (e.g. 'GDP per capita', 'SE.PRM.ENRR', 'WHOSIS_000001')
        source: Data source ('fred', 'world_bank', 'who')
        country: ISO country code for filtering (e.g. 'MX', 'US', 'MEX')
        start_year: Start year filter
        end_year: End year filter
        limit: Maximum results to return (default: 10)
    """
    if source in ("fred", "economic"):
        series = await _service.search_economic_data(query, limit)
        return json.dumps(
            {
                "source": "FRED",
                "query": query,
                "count": len(series),
                "series": [
                    {
                        "series_id": s.series_id,
                        "title": s.title,
                        "unit": s.unit,
                        "frequency": s.frequency,
                        "source": s.source,
                    }
                    for s in series
                ],
            }
        )

    if source in ("who", "health"):
        indicators = await _service.search_health_data(query, country, start_year, end_year, limit)
        return json.dumps(
            {
                "source": "WHO",
                "indicator": query,
                "count": len(indicators),
                "data": [asdict(i) for i in indicators],
            }
        )

    # Default: World Bank
    benchmarks = await _service.search_development_data(query, country, start_year, end_year, limit)
    return json.dumps(
        {
            "source": "World Bank",
            "indicator": query,
            "count": len(benchmarks),
            "data": [asdict(b) for b in benchmarks],
        }
    )


async def fetch_benchmark(
    indicator: str,
    source: str = "world_bank",
    country: str | None = None,
    period: str | None = None,
) -> str:
    """Fetch a benchmark value from international data sources.

    Retrieves comparison data points from FRED, World Bank, or WHO
    for use as baseline or reference in impact evaluations.

    Args:
        indicator: Indicator code or name (e.g. 'SE.PRM.ENRR', 'GDP', 'WHOSIS_000001')
        source: Data source ('fred', 'world_bank', 'who')
        country: ISO country code (e.g. 'MX', 'US')
        period: Time period (e.g. '2015-2020')
    """
    results = await _service.fetch_benchmark(indicator, source, country, period)
    return json.dumps(
        {
            "indicator": indicator,
            "source": source,
            "country": country,
            "period": period,
            "count": len(results),
            "benchmarks": results,
        }
    )


async def compare_programs(
    programs: str,
    metric: str,
    alternative: str = "two-sided",
) -> str:
    """Compare social programs on a metric with statistical testing.

    Accepts program data with outcome values and computes descriptive
    statistics plus significance testing (auto-selects t-test/Welch/Mann-Whitney).

    Args:
        programs: JSON array of program objects with 'name' and 'values' fields.
            Example: '[{{"name": "A", "values": [1.2, 1.5]}},
            {{"name": "B", "values": [0.8, 0.9]}}]'
        metric: Name of the metric being compared (e.g. 'enrollment_rate', 'test_scores')
        alternative: Test alternative ('two-sided', 'less', 'greater')
    """
    try:
        parsed = json.loads(programs)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in programs parameter"})

    if not isinstance(parsed, list):
        return json.dumps({"error": "programs must be a JSON array"})

    result = _service.compare_programs(parsed, metric, alternative)
    return json.dumps(result)

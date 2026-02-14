"""Impact Evaluation tools for the investigation engine.

5 tools for causal analysis of social programs: economic indicator
search, benchmark fetching, cross-program comparison, difference-in-
differences estimation, and validity threat assessment.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ehrlich.impact.application.impact_service import ImpactService
from ehrlich.impact.infrastructure.did_estimator import DiDEstimator
from ehrlich.impact.infrastructure.fred_client import FREDClient
from ehrlich.impact.infrastructure.who_client import WHOClient
from ehrlich.impact.infrastructure.worldbank_client import WorldBankClient

_worldbank = WorldBankClient()
_who = WHOClient()
_fred = FREDClient()
_did = DiDEstimator()
_service = ImpactService(
    economic=_fred,
    health=_who,
    development=_worldbank,
    causal_estimator=_did,
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


async def estimate_did(
    treatment_pre: str,
    treatment_post: str,
    control_pre: str,
    control_post: str,
) -> str:
    """Estimate causal effect using difference-in-differences (DiD).

    Computes the DiD estimator with standard error, p-value, Cohen's d,
    95% confidence interval, parallel trends test, and automated threat
    assessment. Returns evidence tier classification (WWC standards).

    Args:
        treatment_pre: JSON array of pre-intervention treatment values
            (e.g. '[85.2, 87.1, 86.5]')
        treatment_post: JSON array of post-intervention treatment values
            (e.g. '[92.3, 94.1, 93.5]')
        control_pre: JSON array of pre-intervention control values
            (e.g. '[84.0, 85.2, 84.8]')
        control_post: JSON array of post-intervention control values
            (e.g. '[85.1, 85.8, 85.3]')
    """
    try:
        t_pre = [float(x) for x in json.loads(treatment_pre)]
        t_post = [float(x) for x in json.loads(treatment_post)]
        c_pre = [float(x) for x in json.loads(control_pre)]
        c_post = [float(x) for x in json.loads(control_post)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON arrays. Provide numeric arrays."})

    if not all([t_pre, t_post, c_pre, c_post]):
        return json.dumps({"error": "All four groups must have at least one value."})

    estimate = _service.estimate_did(t_pre, t_post, c_pre, c_post)
    result = asdict(estimate)
    # Convert tuple fields to lists for JSON
    result["confidence_interval"] = list(result["confidence_interval"])
    result["covariates"] = list(result["covariates"])
    result["assumptions"] = list(result["assumptions"])
    result["threats"] = [asdict(t) for t in estimate.threats]
    return json.dumps(result)


async def assess_threats(
    method: str,
    sample_sizes: str,
    parallel_trends_p: float | None = None,
    effect_size: float | None = None,
) -> str:
    """Assess validity threats for a causal inference method.

    Knowledge-based threat assessment that identifies potential biases
    and suggests mitigations for different causal methods (DiD, PSM,
    RDD, RCT, IV).

    Args:
        method: Causal method name ('did', 'psm', 'rdd', 'rct', 'iv')
        sample_sizes: JSON object mapping group names to sizes
            (e.g. '{{"treatment": 50, "control": 45}}')
        parallel_trends_p: p-value from parallel trends test (DiD only)
        effect_size: Cohen's d or standardized effect size
    """
    try:
        sizes = json.loads(sample_sizes)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in sample_sizes parameter"})

    if not isinstance(sizes, dict):
        return json.dumps({"error": "sample_sizes must be a JSON object"})

    parsed_sizes = {str(k): int(v) for k, v in sizes.items()}
    threats = _service.assess_threats(method, parsed_sizes, parallel_trends_p, effect_size)
    return json.dumps({
        "method": method,
        "threat_count": len(threats),
        "threats": [asdict(t) for t in threats],
    })

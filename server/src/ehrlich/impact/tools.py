"""Impact Evaluation tools for the investigation engine.

11 tools for social program data retrieval: economic indicator search,
health indicator search, benchmark fetching, cross-program comparison,
spending data, education data, housing data, open data discovery,
INEGI economic data, Banxico financial series, datos.gob.mx open data,
and CONEVAL/CREMAA indicator analysis.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ehrlich.impact.application.impact_service import ImpactService
from ehrlich.impact.infrastructure.banxico_client import BanxicoClient
from ehrlich.impact.infrastructure.bls_client import BLSClient
from ehrlich.impact.infrastructure.cdc_client import CDCWonderClient
from ehrlich.impact.infrastructure.census_client import CensusClient
from ehrlich.impact.infrastructure.college_scorecard_client import CollegeScorecardClient
from ehrlich.impact.infrastructure.datagov_client import DataGovClient
from ehrlich.impact.infrastructure.datosgob_client import DatosGobClient
from ehrlich.impact.infrastructure.fred_client import FREDClient
from ehrlich.impact.infrastructure.hud_client import HUDClient
from ehrlich.impact.infrastructure.inegi_client import INEGIClient
from ehrlich.impact.infrastructure.usaspending_client import USAspendingClient
from ehrlich.impact.infrastructure.who_client import WHOClient
from ehrlich.impact.infrastructure.worldbank_client import WorldBankClient

_worldbank = WorldBankClient()
_who = WHOClient()
_fred = FREDClient()
_bls = BLSClient()
_census = CensusClient()
_usaspending = USAspendingClient()
_scorecard = CollegeScorecardClient()
_hud = HUDClient()
_cdc = CDCWonderClient()
_datagov = DataGovClient()
_inegi = INEGIClient()
_banxico = BanxicoClient()
_datosgob = DatosGobClient()

_service = ImpactService(
    economic=_fred,
    health=_who,
    development=_worldbank,
    spending=_usaspending,
    education=_scorecard,
    housing=_hud,
    open_data=_datagov,
    bls=_bls,
    census=_census,
    cdc=_cdc,
    inegi=_inegi,
    banxico=_banxico,
    datosgob=_datosgob,
)


async def search_economic_indicators(
    query: str,
    source: str = "fred",
    country: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    limit: int = 10,
) -> str:
    """Search FRED, BLS, Census, World Bank, WHO, INEGI, or Banxico for economic indicators.

    Queries the specified data source for time series data relevant to
    impact evaluation. Returns series metadata and values for analysis.

    Args:
        query: Search query or indicator code
            (e.g. 'GDP per capita', 'SE.PRM.ENRR', 'WHOSIS_000001',
            'LNS14000000' for BLS, 'median_income' for Census,
            'inflacion' or indicator ID for INEGI,
            'tipo de cambio' or series ID for Banxico)
        source: Data source ('fred', 'bls', 'census', 'world_bank', 'who',
            'inegi', 'banxico')
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

    if source == "bls":
        series = await _service.search_bls_data(query, limit)
        return json.dumps(
            {
                "source": "BLS",
                "query": query,
                "count": len(series),
                "series": [
                    {
                        "series_id": s.series_id,
                        "title": s.title,
                        "values_count": len(s.values),
                        "source": s.source,
                    }
                    for s in series
                ],
            }
        )

    if source == "census":
        benchmarks = await _service.search_census_data(query, country, start_year, end_year, limit)
        return json.dumps(
            {
                "source": "Census",
                "indicator": query,
                "count": len(benchmarks),
                "data": [asdict(b) for b in benchmarks],
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

    if source == "inegi":
        series = await _service.search_inegi_data(query, limit)
        return json.dumps(
            {
                "source": "INEGI",
                "query": query,
                "count": len(series),
                "series": [
                    {
                        "series_id": s.series_id,
                        "title": s.title,
                        "unit": s.unit,
                        "frequency": s.frequency,
                        "values_count": len(s.values),
                        "source": s.source,
                    }
                    for s in series
                ],
            }
        )

    if source == "banxico":
        series = await _service.search_banxico_data(query, limit)
        return json.dumps(
            {
                "source": "Banxico",
                "query": query,
                "count": len(series),
                "series": [
                    {
                        "series_id": s.series_id,
                        "title": s.title,
                        "values_count": len(s.values),
                        "source": s.source,
                    }
                    for s in series
                ],
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


async def search_health_indicators(
    indicator: str,
    source: str = "who",
    country: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    limit: int = 10,
) -> str:
    """Search WHO GHO or CDC WONDER for health indicators.

    Args:
        indicator: Indicator code or name (e.g. 'WHOSIS_000001' for WHO,
            'mortality' or 'natality' for CDC WONDER)
        source: Data source ('who', 'cdc')
        country: ISO country code (WHO only, e.g. 'MEX', 'USA')
        year_start: Start year filter
        year_end: End year filter
        limit: Maximum results to return (default: 10)
    """
    if source == "cdc":
        results = await _service.search_cdc_data(indicator, year_start, year_end, limit)
        return json.dumps(
            {
                "source": "CDC WONDER",
                "indicator": indicator,
                "count": len(results),
                "data": [asdict(r) for r in results],
            }
        )

    results = await _service.search_health_data(indicator, country, year_start, year_end, limit)
    return json.dumps(
        {
            "source": "WHO",
            "indicator": indicator,
            "count": len(results),
            "data": [asdict(r) for r in results],
        }
    )


async def fetch_benchmark(
    indicator: str,
    source: str = "world_bank",
    country: str | None = None,
    period: str | None = None,
) -> str:
    """Fetch a benchmark value from international or US data sources.

    Retrieves comparison data points from FRED, BLS, Census, World Bank,
    WHO, or CDC for use as baseline or reference in impact evaluations.

    Args:
        indicator: Indicator code or name (e.g. 'SE.PRM.ENRR', 'GDP',
            'LNS14000000', 'median_income', 'mortality')
        source: Data source ('fred', 'bls', 'census', 'world_bank', 'who', 'cdc')
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


async def search_spending_data(
    query: str,
    agency: str | None = None,
    year: int | None = None,
    award_type: str | None = None,
    limit: int = 10,
) -> str:
    """Search USAspending.gov for federal spending awards and grants.

    Args:
        query: Search keywords (e.g. 'Head Start', 'SNAP', 'education grants')
        agency: Federal agency name filter (e.g. 'Department of Education')
        year: Fiscal year filter (e.g. 2023)
        award_type: Type filter (unused, reserved for future filtering)
        limit: Maximum results to return (default: 10)
    """
    records = await _service.search_spending_data(query, agency, year, limit)
    return json.dumps(
        {
            "source": "USAspending",
            "query": query,
            "count": len(records),
            "awards": [asdict(r) for r in records],
        }
    )


async def search_education_data(
    query: str,
    state: str | None = None,
    fields: str | None = None,
    limit: int = 10,
) -> str:
    """Search College Scorecard for US higher education institution data.

    Args:
        query: School name search (e.g. 'Harvard', 'community college')
        state: State abbreviation filter (e.g. 'CA', 'NY')
        fields: Unused, reserved for future field selection
        limit: Maximum results to return (default: 10)
    """
    records = await _service.search_education_data(query, state, limit)
    return json.dumps(
        {
            "source": "College Scorecard",
            "query": query,
            "count": len(records),
            "schools": [asdict(r) for r in records],
        }
    )


async def search_housing_data(
    state: str,
    county: str | None = None,
    year: int | None = None,
    data_type: str = "fmr",
) -> str:
    """Search HUD for housing data (Fair Market Rents, income limits).

    Args:
        state: State abbreviation (e.g. 'CA', 'TX')
        county: County FIPS code (optional)
        year: FMR year (default: most recent)
        data_type: Data type ('fmr' for Fair Market Rents)
    """
    records = await _service.search_housing_data(state, county, year)
    return json.dumps(
        {
            "source": "HUD",
            "state": state,
            "data_type": data_type,
            "count": len(records),
            "data": [asdict(r) for r in records],
        }
    )


async def search_open_data(
    query: str,
    organization: str | None = None,
    source: str = "datagov",
    limit: int = 10,
) -> str:
    """Search data.gov or datos.gob.mx CKAN catalog for open datasets.

    Discovers available datasets for further analysis. Returns metadata
    including title, organization, tags, and resource counts.

    Args:
        query: Search keywords (e.g. 'poverty', 'education outcomes',
            'programa social', 'salud')
        organization: Organization filter (e.g. 'hhs-gov' for data.gov,
            'sedesol' for datos.gob.mx)
        source: Data source ('datagov' for US data.gov, 'datosgob' for
            Mexico datos.gob.mx)
        limit: Maximum results to return (default: 10)
    """
    if source == "datosgob":
        records = await _service.search_mexican_open_data(query, organization, limit)
        catalog_name = "datos.gob.mx"
    else:
        records = await _service.search_open_data(query, organization, limit)
        catalog_name = "data.gov"

    return json.dumps(
        {
            "source": catalog_name,
            "query": query,
            "count": len(records),
            "datasets": [
                {
                    "dataset_id": r.dataset_id,
                    "title": r.title,
                    "organization": r.organization,
                    "description": r.description,
                    "tags": list(r.tags),
                    "resource_count": r.resource_count,
                    "modified": r.modified,
                }
                for r in records
            ],
        }
    )


async def analyze_program_indicators(
    indicator_name: str,
    level: str,
) -> str:
    """Validate a MIR indicator against CREMAA quality criteria (CONEVAL methodology).

    Evaluates an indicator name against all 6 CREMAA criteria at the
    specified MIR level (fin, proposito, componente, actividad).
    Returns structured guidance for each criterion.

    Args:
        indicator_name: Name of the indicator to evaluate
            (e.g. 'Porcentaje de beneficiarios que mejoran su nivel educativo')
        level: MIR logic model level ('fin', 'proposito', 'componente', 'actividad')
    """
    result = _service.analyze_program_indicators(indicator_name, level)
    return json.dumps(result)

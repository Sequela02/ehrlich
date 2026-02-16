import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import Benchmark
from ehrlich.impact.domain.repository import DevelopmentDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.census.gov/data"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

_ACS_VARIABLES = {
    "population": "B01003_001E",
    "median_income": "B19013_001E",
    "poverty_rate": "B17001_002E",
    "bachelors_degree": "B15003_022E",
    "unemployment": "B23025_005E",
}


class CensusClient(DevelopmentDataRepository):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("CENSUS_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[Benchmark]:
        variable = _ACS_VARIABLES.get(indicator.lower(), indicator)
        year = year_end or 2022
        geo = country or "us"

        params: dict[str, str] = {
            "get": f"NAME,{variable}",
            "for": "state:*" if geo == "us" else f"state:{geo}",
        }
        if self._api_key:
            params["key"] = self._api_key

        data = await self._get(f"{_BASE_URL}/{year}/acs/acs5", params=params)
        if not isinstance(data, list) or len(data) < 2:
            return []

        raw_headers = data[0]
        header_list = raw_headers if isinstance(raw_headers, list) else []
        indicator_name = str(header_list[1]) if len(header_list) > 1 else variable
        results: list[Benchmark] = []
        for row in data[1 : limit + 1]:
            if not isinstance(row, list) or len(row) < 2:
                continue
            try:
                value = float(row[1])
            except (ValueError, TypeError):
                continue
            name = str(row[0]) if row[0] else ""
            results.append(
                Benchmark(
                    source="census",
                    indicator=indicator_name,
                    value=value,
                    unit="",
                    geography=name,
                    period=str(year),
                    url=f"https://data.census.gov/table?q={variable}",
                )
            )
        return results

    async def get_countries(self) -> list[dict[str, str]]:
        return []

    async def _get(self, url: str, params: dict[str, str]) -> list[object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Census rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("Census", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "Census timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("Census", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "Census",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

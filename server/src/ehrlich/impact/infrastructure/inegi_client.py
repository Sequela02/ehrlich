import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import DataPoint, EconomicSeries
from ehrlich.impact.domain.repository import EconomicDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

# Common INEGI indicator IDs for search fallback
_KNOWN_INDICATORS: dict[str, str] = {
    "pib": "493911",
    "gdp": "493911",
    "inflacion": "910406",
    "inflation": "910406",
    "desempleo": "444612",
    "unemployment": "444612",
    "poblacion": "1002000001",
    "population": "1002000001",
}


class INEGIClient(EconomicDataRepository):
    def __init__(self, api_token: str | None = None) -> None:
        self._token = api_token or os.environ.get("INEGI_API_TOKEN", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_series(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._token:
            return []
        # Resolve known keyword -> indicator ID; fallback to raw query as indicator ID
        indicator_id = _KNOWN_INDICATORS.get(query.lower().strip(), query.strip())
        series = await self.get_series(indicator_id)
        return [series] if series else []

    async def get_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None:
        if not self._token:
            return None
        url = f"{_BASE_URL}/{series_id}/es/0700/true/bib/{self._token}"
        data = await self._get(url, {"type": "json"})

        series_list = data.get("Series", [])
        if not isinstance(series_list, list) or not series_list:
            return None

        first = series_list[0]
        if not isinstance(first, dict):
            return None

        obs_list = first.get("OBSERVATIONS", [])
        points: list[DataPoint] = []
        if isinstance(obs_list, list):
            for obs in obs_list:
                if not isinstance(obs, dict):
                    continue
                time_period = str(obs.get("TIME_PERIOD", ""))
                if start and time_period < start:
                    continue
                if end and time_period > end:
                    continue
                raw_val = obs.get("OBS_VALUE", "")
                try:
                    value = float(raw_val)
                except (ValueError, TypeError):
                    continue
                points.append(DataPoint(date=time_period, value=value))

        indicator_name = str(first.get("LASTUPDATE", series_id))
        return EconomicSeries(
            series_id=series_id,
            title=indicator_name,
            values=tuple(points),
            source="inegi",
            unit=str(first.get("UNIT", "")),
            frequency=str(first.get("FREQ", "")),
        )

    async def _get(self, url: str, params: dict[str, str]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "INEGI rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("INEGI", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "INEGI timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("INEGI", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "INEGI",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

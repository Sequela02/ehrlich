import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import DataPoint, EconomicSeries
from ehrlich.impact.domain.repository import EconomicDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stlouisfed.org/fred"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class FREDClient(EconomicDataRepository):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_series(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._api_key:
            return []
        data = await self._get(
            f"{_BASE_URL}/series/search",
            params={
                "search_text": query,
                "api_key": self._api_key,
                "file_type": "json",
                "limit": min(limit, 100),
            },
        )
        items = data.get("seriess", [])
        if not isinstance(items, list):
            return []
        return [
            EconomicSeries(
                series_id=str(s.get("id", "")),
                title=str(s.get("title", "")),
                values=(),
                source="fred",
                unit=str(s.get("units", "")),
                frequency=str(s.get("frequency", "")),
            )
            for s in items[:limit]
            if isinstance(s, dict)
        ]

    async def get_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None:
        if not self._api_key:
            return None
        params: dict[str, str | int] = {
            "series_id": series_id,
            "api_key": self._api_key,
            "file_type": "json",
        }
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end

        data = await self._get(f"{_BASE_URL}/series/observations", params=params)
        observations = data.get("observations", [])
        if not isinstance(observations, list):
            return None

        points: list[DataPoint] = []
        for obs in observations:
            if not isinstance(obs, dict):
                continue
            value_raw = obs.get("value", ".")
            if value_raw == ".":
                continue
            try:
                value = float(value_raw)
            except (ValueError, TypeError):
                continue
            points.append(DataPoint(date=str(obs.get("date", "")), value=value))

        return EconomicSeries(
            series_id=series_id,
            title=series_id,
            values=tuple(points),
            source="fred",
            unit="",
            frequency="",
        )

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "FRED rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("FRED", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "FRED timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("FRED", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "FRED",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

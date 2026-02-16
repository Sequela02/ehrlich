import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import DataPoint, EconomicSeries
from ehrlich.impact.domain.repository import EconomicDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class BLSClient(EconomicDataRepository):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("BLS_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_series(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._api_key:
            return []
        series_ids = [s.strip() for s in query.split(",")][:limit]
        data = await self._post(series_ids)
        return self._parse_series(data, series_ids)

    async def get_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None:
        if not self._api_key:
            return None
        body: dict[str, object] = {
            "seriesid": [series_id],
            "registrationkey": self._api_key,
        }
        if start:
            body["startyear"] = start[:4]
        if end:
            body["endyear"] = end[:4]

        data = await self._post_body(body)
        results = self._parse_series(data, [series_id])
        return results[0] if results else None

    def _parse_series(self, data: dict[str, object], series_ids: list[str]) -> list[EconomicSeries]:
        results_obj = data.get("Results", {})
        if not isinstance(results_obj, dict):
            return []
        series_list = results_obj.get("series", [])
        if not isinstance(series_list, list):
            return []

        results: list[EconomicSeries] = []
        for s in series_list:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("seriesID", ""))
            raw_data = s.get("data", [])
            points: list[DataPoint] = []
            if isinstance(raw_data, list):
                for d in raw_data:
                    if not isinstance(d, dict):
                        continue
                    try:
                        value = float(d.get("value", "0"))
                    except (ValueError, TypeError):
                        continue
                    year = str(d.get("year", ""))
                    period = str(d.get("period", ""))
                    points.append(DataPoint(date=f"{year}-{period}", value=value))

            results.append(
                EconomicSeries(
                    series_id=sid,
                    title=sid,
                    values=tuple(points),
                    source="bls",
                    unit="",
                    frequency="",
                )
            )
        return results

    async def _post(self, series_ids: list[str]) -> dict[str, object]:
        body: dict[str, object] = {
            "seriesid": series_ids,
            "registrationkey": self._api_key,
        }
        return await self._post_body(body)

    async def _post_body(self, body: dict[str, object]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(_BASE_URL, json=body)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "BLS rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("BLS", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "BLS timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("BLS", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "BLS",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

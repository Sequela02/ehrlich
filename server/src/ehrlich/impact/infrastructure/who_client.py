import asyncio
import logging

import httpx

from ehrlich.impact.domain.entities import HealthIndicator
from ehrlich.impact.domain.repository import HealthDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://ghoapi.azureedge.net/api"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class WHOClient(HealthDataRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[HealthIndicator]:
        filters: list[str] = []
        if country:
            filters.append(f"SpatialDim eq '{country}'")
        if year_start:
            filters.append(f"TimeDim ge {year_start}")
        if year_end:
            filters.append(f"TimeDim le {year_end}")

        params: dict[str, str | int] = {"$top": min(limit, 100)}
        if filters:
            params["$filter"] = " and ".join(filters)

        data = await self._get(f"{_BASE_URL}/{indicator}", params=params)
        items = data.get("value", [])
        if not isinstance(items, list):
            return []

        results: list[HealthIndicator] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            value_raw = item.get("NumericValue")
            if value_raw is None:
                continue
            try:
                value = float(value_raw)
            except (ValueError, TypeError):
                continue
            try:
                year = int(item.get("TimeDim", 0))
            except (ValueError, TypeError):
                year = 0

            results.append(
                HealthIndicator(
                    indicator_code=indicator,
                    indicator_name=str(item.get("IndicatorCode", indicator)),
                    country=str(item.get("SpatialDim", "")),
                    year=year,
                    value=value,
                    unit=str(item.get("Dim1", "")),
                )
            )
        return results

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "WHO GHO rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("WHO GHO", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "WHO GHO timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("WHO GHO", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "WHO GHO",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

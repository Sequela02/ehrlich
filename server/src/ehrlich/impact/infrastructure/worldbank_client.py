import asyncio
import logging

import httpx

from ehrlich.impact.domain.entities import Benchmark
from ehrlich.impact.domain.repository import DevelopmentDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.worldbank.org/v2"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class WorldBankClient(DevelopmentDataRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[Benchmark]:
        iso = country or "all"
        params: dict[str, str | int] = {
            "format": "json",
            "per_page": min(limit, 100),
        }
        if year_start and year_end:
            params["date"] = f"{year_start}:{year_end}"

        data = await self._get(
            f"{_BASE_URL}/country/{iso}/indicator/{indicator}",
            params=params,
        )

        # World Bank returns [metadata, data_array] or [metadata]
        if not isinstance(data, list) or len(data) < 2:
            return []

        items = data[1]
        if not isinstance(items, list):
            return []

        results: list[Benchmark] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            value_raw = item.get("value")
            if value_raw is None:
                continue
            try:
                value = float(value_raw)
            except (ValueError, TypeError):
                continue

            country_info = item.get("country", {})
            country_name = country_info.get("value", "") if isinstance(country_info, dict) else ""
            indicator_info = item.get("indicator", {})
            indicator_name = (
                indicator_info.get("value", "") if isinstance(indicator_info, dict) else ""
            )

            results.append(
                Benchmark(
                    source="world_bank",
                    indicator=indicator_name or indicator,
                    value=value,
                    unit=str(item.get("unit", "")),
                    geography=country_name,
                    period=str(item.get("date", "")),
                    url=f"https://data.worldbank.org/indicator/{indicator}",
                )
            )
        return results

    async def get_countries(self) -> list[dict[str, str]]:
        data = await self._get(
            f"{_BASE_URL}/country",
            params={"format": "json", "per_page": 300},
        )
        if not isinstance(data, list) or len(data) < 2:
            return []
        items = data[1]
        if not isinstance(items, list):
            return []
        return [
            {
                "id": str(c.get("id", "")),
                "name": str(c.get("name", "")),
                "region": str((c.get("region") or {}).get("value", "")),
                "income_level": str((c.get("incomeLevel") or {}).get("value", "")),
            }
            for c in items
            if isinstance(c, dict)
        ]

    async def _get(
        self, url: str, params: dict[str, str | int]
    ) -> list[object] | dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "World Bank rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("World Bank", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "World Bank timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("World Bank", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "World Bank",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

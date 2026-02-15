import asyncio
import logging

import httpx

from ehrlich.impact.domain.entities import SpendingRecord
from ehrlich.impact.domain.repository import SpendingDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.usaspending.gov/api/v2"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class USAspendingClient(SpendingDataRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_awards(
        self,
        query: str,
        agency: str | None = None,
        year: int | None = None,
        limit: int = 10,
    ) -> list[SpendingRecord]:
        filters: dict[str, object] = {"keyword": query}
        if agency:
            filters["agencies"] = [
                {"type": "awarding", "tier": "toptier", "name": agency}
            ]
        if year:
            filters["time_period"] = [
                {"start_date": f"{year}-01-01", "end_date": f"{year}-12-31"}
            ]

        body: dict[str, object] = {
            "filters": filters,
            "limit": min(limit, 100),
            "page": 1,
        }

        data = await self._post(f"{_BASE_URL}/search/spending_by_award/", body)
        results_list = data.get("results", [])
        if not isinstance(results_list, list):
            return []

        records: list[SpendingRecord] = []
        for item in results_list[:limit]:
            if not isinstance(item, dict):
                continue
            try:
                amount = float(item.get("Award Amount") or item.get("Total Outlays", 0))
            except (ValueError, TypeError):
                amount = 0.0

            records.append(
                SpendingRecord(
                    award_id=str(item.get("Award ID") or item.get("internal_id", "")),
                    recipient_name=str(item.get("Recipient Name", "")),
                    amount=amount,
                    agency=str(item.get("Awarding Agency", "")),
                    description=str(item.get("Award Type", "")),
                    period=str(item.get("Start Date", "")),
                    award_type=str(item.get("Award Type", "")),
                )
            )
        return records

    async def _post(self, url: str, body: dict[str, object]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(url, json=body)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "USAspending rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("USAspending", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "USAspending timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "USAspending", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "USAspending",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

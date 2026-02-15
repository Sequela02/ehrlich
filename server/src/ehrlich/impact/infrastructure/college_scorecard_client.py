import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import EducationRecord
from ehrlich.impact.domain.repository import EducationDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class CollegeScorecardClient(EducationDataRepository):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("COLLEGE_SCORECARD_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_schools(
        self,
        query: str,
        state: str | None = None,
        limit: int = 10,
    ) -> list[EducationRecord]:
        if not self._api_key:
            return []

        params: dict[str, str | int] = {
            "api_key": self._api_key,
            "school.name": query,
            "fields": (
                "id,school.name,school.state,"
                "latest.student.size,"
                "latest.cost.avg_net_price.overall,"
                "latest.completion.rate_suppressed.overall,"
                "latest.earnings.10_yrs_after_entry.median"
            ),
            "per_page": min(limit, 100),
        }
        if state:
            params["school.state"] = state

        data = await self._get(params)
        results_list = data.get("results", [])
        if not isinstance(results_list, list):
            return []

        records: list[EducationRecord] = []
        for item in results_list[:limit]:
            if not isinstance(item, dict):
                continue

            latest = item.get("latest", {})
            if not isinstance(latest, dict):
                latest = {}
            student = latest.get("student", {})
            cost = latest.get("cost", {})
            completion = latest.get("completion", {})
            earnings = latest.get("earnings", {})

            school = item.get("school", {})
            if not isinstance(school, dict):
                school = {}

            def _float(obj: object, *keys: str) -> float:
                current = obj
                for k in keys:
                    if isinstance(current, dict):
                        current = current.get(k)
                    else:
                        return 0.0
                try:
                    return float(current)  # type: ignore[arg-type]
                except (ValueError, TypeError):
                    return 0.0

            def _int(obj: object, *keys: str) -> int:
                current = obj
                for k in keys:
                    if isinstance(current, dict):
                        current = current.get(k)
                    else:
                        return 0
                try:
                    return int(str(current))
                except (ValueError, TypeError):
                    return 0

            records.append(
                EducationRecord(
                    school_id=str(item.get("id", "")),
                    name=str(school.get("name", "")),
                    state=str(school.get("state", "")),
                    student_size=_int(student, "size"),
                    net_price=_float(cost, "avg_net_price", "overall"),
                    completion_rate=_float(completion, "rate_suppressed", "overall"),
                    earnings_median=_float(earnings, "10_yrs_after_entry", "median"),
                )
            )
        return records

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(_BASE_URL, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "College Scorecard rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("College Scorecard", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "College Scorecard timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "College Scorecard", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "College Scorecard",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

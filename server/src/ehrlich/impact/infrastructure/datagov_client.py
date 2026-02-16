import asyncio
import logging

import httpx

from ehrlich.impact.domain.entities import DatasetMetadata
from ehrlich.impact.domain.repository import OpenDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://catalog.data.gov/api/3/action"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class DataGovClient(OpenDataRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_datasets(
        self,
        query: str,
        organization: str | None = None,
        limit: int = 10,
    ) -> list[DatasetMetadata]:
        params: dict[str, str | int] = {
            "q": query,
            "rows": min(limit, 100),
        }
        if organization:
            params["fq"] = f"organization:{organization}"

        data = await self._get(f"{_BASE_URL}/package_search", params)
        result_obj = data.get("result", {})
        if not isinstance(result_obj, dict):
            return []
        results_list = result_obj.get("results", [])
        if not isinstance(results_list, list):
            return []

        records: list[DatasetMetadata] = []
        for item in results_list[:limit]:
            if not isinstance(item, dict):
                continue

            org = item.get("organization", {})
            org_title = org.get("title", "") if isinstance(org, dict) else ""
            raw_tags = item.get("tags", [])
            tags: list[str] = []
            if isinstance(raw_tags, list):
                for t in raw_tags:
                    if isinstance(t, dict):
                        tags.append(str(t.get("name", "")))
                    elif isinstance(t, str):
                        tags.append(t)

            resources = item.get("resources", [])
            resource_count = len(resources) if isinstance(resources, list) else 0

            records.append(
                DatasetMetadata(
                    dataset_id=str(item.get("id", "")),
                    title=str(item.get("title", "")),
                    organization=str(org_title),
                    description=str(item.get("notes", ""))[:500],
                    tags=tuple(tags),
                    resource_count=resource_count,
                    modified=str(item.get("metadata_modified", "")),
                )
            )
        return records

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "data.gov rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("data.gov", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "data.gov timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("data.gov", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "data.gov",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

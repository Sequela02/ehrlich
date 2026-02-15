import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import HousingData
from ehrlich.impact.domain.repository import HousingDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.huduser.gov/hudapi/public"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class HUDClient(HousingDataRepository):
    def __init__(self, api_token: str | None = None) -> None:
        self._token = api_token or os.environ.get("HUD_API_TOKEN", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_housing_data(
        self,
        state: str,
        county: str | None = None,
        year: int | None = None,
    ) -> list[HousingData]:
        if not self._token:
            return []

        entity_id = f"{county},{state}" if county else state
        fmr_year = year or 2024
        endpoint = f"{_BASE_URL}/fmr/statedata/{entity_id}"
        params: dict[str, str | int] = {"year": fmr_year}

        data = await self._get(endpoint, params)
        fmr_data = data.get("data", {})

        if isinstance(fmr_data, dict):
            items = [fmr_data]
        elif isinstance(fmr_data, list):
            items = fmr_data
        else:
            return []

        results: list[HousingData] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append(self._parse_housing(item, state, fmr_year))
        return results

    @staticmethod
    def _parse_housing(item: dict[str, object], state: str, year: int) -> HousingData:
        def _fmr(key: str) -> float:
            try:
                return float(item.get(key, 0))  # type: ignore[arg-type]
            except (ValueError, TypeError):
                return 0.0

        return HousingData(
            area_name=str(item.get("area_name") or item.get("areaname", "")),
            state=state.upper(),
            fmr_0br=_fmr("fmr_0"),
            fmr_1br=_fmr("fmr_1"),
            fmr_2br=_fmr("fmr_2"),
            fmr_3br=_fmr("fmr_3"),
            fmr_4br=_fmr("fmr_4"),
            median_income=_fmr("median_income"),
            year=year,
        )

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {self._token}"}
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params, headers=headers)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "HUD rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("HUD", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "HUD timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("HUD", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "HUD",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

import asyncio
import logging
import os

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.sports.domain.entities import NutrientEntry, NutrientProfile
from ehrlich.sports.domain.repository import NutrientRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class FoodDataClient(NutrientRepository):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("USDA_API_KEY", "DEMO_KEY")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, query: str, max_results: int = 5
    ) -> list[NutrientProfile]:
        data = await self._get(
            f"{_BASE_URL}/foods/search",
            params={
                "query": query,
                "pageSize": min(max_results, 25),
                "api_key": self._api_key,
            },
        )
        foods = data.get("foods", [])
        if not isinstance(foods, list):
            foods = []
        return [
            self._parse_food(f)
            for f in foods[:max_results]
            if isinstance(f, dict)
        ]

    async def _get(
        self, url: str, params: dict[str, str | int]
    ) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "USDA FoodData rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError(
                        "USDA FoodData", "Rate limit exceeded"
                    )
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "USDA FoodData timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "USDA FoodData", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "USDA FoodData",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_food(food: dict[str, object]) -> NutrientProfile:
        try:
            fdc_id = int(str(food.get("fdcId", 0)))
        except (ValueError, TypeError):
            fdc_id = 0

        nutrients_raw = food.get("foodNutrients", [])
        nutrients = nutrients_raw if isinstance(nutrients_raw, list) else []

        parsed: list[NutrientEntry] = []
        for n in nutrients:
            if not isinstance(n, dict):
                continue
            try:
                amount = float(n.get("value", 0))
            except (ValueError, TypeError):
                amount = 0.0
            parsed.append(
                NutrientEntry(
                    name=str(n.get("nutrientName", "")),
                    amount=amount,
                    unit=str(n.get("unitName", "")),
                    nutrient_number=str(n.get("nutrientNumber", "")),
                )
            )

        return NutrientProfile(
            fdc_id=fdc_id,
            description=str(food.get("description", "")),
            brand=str(food.get("brandName", "") or food.get("brandOwner", "") or ""),
            category=str(food.get("foodCategory", "") or ""),
            nutrients=tuple(parsed),
        )

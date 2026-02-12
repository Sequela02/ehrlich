import asyncio
import contextlib
import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.sports.domain.entities import IngredientEntry, SupplementLabel
from ehrlich.sports.domain.repository import SupplementRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.ods.od.nih.gov/dsld/v9"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class DSLDClient(SupplementRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_labels(
        self, ingredient: str, max_results: int = 10
    ) -> list[SupplementLabel]:
        data = await self._get(
            f"{_BASE_URL}/browse-ingredients",
            params={"query": ingredient, "pagesize": min(max_results, 50)},
        )
        items = data.get("list", [])
        if not isinstance(items, list):
            items = []

        labels: list[SupplementLabel] = []
        for item in items[:max_results]:
            if not isinstance(item, dict):
                continue
            label = self._parse_ingredient_result(item)
            if label:
                labels.append(label)
        return labels

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
                        "NIH DSLD rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError(
                        "NIH DSLD", "Rate limit exceeded"
                    )
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "NIH DSLD timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "NIH DSLD", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "NIH DSLD",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_ingredient_result(item: dict[str, object]) -> SupplementLabel | None:
        report_id = str(item.get("dsld_id", ""))
        if not report_id:
            return None

        product_name = str(item.get("product_name", ""))
        brand = str(item.get("brand_name", ""))
        serving_size = str(item.get("serving_size", ""))

        ingredients_raw = item.get("ingredients", [])
        ingredients = ingredients_raw if isinstance(ingredients_raw, list) else []

        parsed: list[IngredientEntry] = []
        for ing in ingredients:
            if not isinstance(ing, dict):
                continue
            dv_raw = ing.get("daily_value_pct")
            dv: float | None = None
            if dv_raw is not None:
                with contextlib.suppress(ValueError, TypeError):
                    dv = float(dv_raw)
            parsed.append(
                IngredientEntry(
                    name=str(ing.get("name", "")),
                    amount=str(ing.get("amount", "")),
                    unit=str(ing.get("unit", "")),
                    daily_value_pct=dv,
                )
            )

        return SupplementLabel(
            report_id=report_id,
            product_name=product_name,
            brand=brand,
            ingredients=tuple(parsed),
            serving_size=serving_size,
        )

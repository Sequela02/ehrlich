import asyncio
import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.nutrition.domain.entities import AdverseEvent
from ehrlich.nutrition.domain.repository import AdverseEventRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.fda.gov/food/event.json"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class OpenFDAClient(AdverseEventRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, product_name: str, max_results: int = 10
    ) -> list[AdverseEvent]:
        safe_name = product_name.replace('"', '\\"')
        params: dict[str, str | int] = {
            "search": f'products.name_brand:"{safe_name}"',
            "limit": min(max_results, 100),
        }
        data = await self._get(params)
        results = data.get("results", [])
        if not isinstance(results, list):
            results = []
        return [
            self._parse_event(e)
            for e in results[:max_results]
            if isinstance(e, dict)
        ]

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(_BASE_URL, params=params)
                if resp.status_code == 404:
                    return {"results": []}
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "OpenFDA rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError(
                        "OpenFDA", "Rate limit exceeded"
                    )
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "OpenFDA timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "OpenFDA", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "OpenFDA",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_event(event: dict[str, object]) -> AdverseEvent:
        products_raw = event.get("products", [])
        products = products_raw if isinstance(products_raw, list) else []

        reactions_raw = event.get("reactions", [])
        reactions = reactions_raw if isinstance(reactions_raw, list) else []

        outcomes_raw = event.get("outcomes", [])
        outcomes = outcomes_raw if isinstance(outcomes_raw, list) else []

        consumer = event.get("consumer", {})
        if not isinstance(consumer, dict):
            consumer = {}

        return AdverseEvent(
            report_id=str(event.get("report_number", "")),
            date=str(event.get("date_started", "")),
            products=tuple(
                str(p.get("name_brand", "")) if isinstance(p, dict) else str(p)
                for p in products
            ),
            reactions=tuple(
                str(r.get("reaction", "")) if isinstance(r, dict) else str(r)
                for r in reactions
            ),
            outcomes=tuple(str(o) for o in outcomes),
            consumer_age=str(consumer.get("age", "")),
            consumer_gender=str(consumer.get("gender", "")),
        )

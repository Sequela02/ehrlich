from __future__ import annotations

import asyncio
import logging
import re

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.training.domain.entities import Exercise
from ehrlich.training.domain.repository import ExerciseRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://wger.de/api/v2"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

_MUSCLE_IDS: dict[str, int] = {
    "chest": 4,
    "biceps": 1,
    "triceps": 5,
    "shoulders": 2,
    "quadriceps": 10,
    "hamstrings": 11,
    "glutes": 8,
    "calves": 15,
    "abdominals": 6,
    "back": 12,
    "lats": 14,
    "forearms": 13,
    "trapezius": 9,
}

_CATEGORY_IDS: dict[str, int] = {
    "abs": 10,
    "arms": 8,
    "back": 12,
    "calves": 14,
    "cardio": 15,
    "chest": 11,
    "legs": 9,
    "shoulders": 13,
    "stretching": 16,
}

_EQUIPMENT_IDS: dict[str, int] = {
    "barbell": 1,
    "dumbbell": 3,
    "gym_mat": 4,
    "kettlebell": 10,
    "pull_up_bar": 6,
    "bench": 8,
    "bodyweight": 7,
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


class WgerClient(ExerciseRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, muscle_group: str = "", equipment: str = "", category: str = "", limit: int = 20
    ) -> list[Exercise]:
        params: dict[str, str | int] = {
            "format": "json",
            "language": 2,
            "limit": limit,
        }
        if muscle_group:
            muscle_id = _MUSCLE_IDS.get(muscle_group.lower())
            if muscle_id:
                params["muscles"] = muscle_id
        if equipment:
            eq_id = _EQUIPMENT_IDS.get(equipment.lower())
            if eq_id:
                params["equipment"] = eq_id
        if category:
            cat_id = _CATEGORY_IDS.get(category.lower())
            if cat_id:
                params["category"] = cat_id

        data = await self._get(params)
        results_raw = data.get("results", [])
        results = results_raw if isinstance(results_raw, list) else []
        return [self._parse_exercise(e) for e in results if isinstance(e, dict)]

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        url = f"{_BASE_URL}/exercise/"
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "wger rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("wger", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "wger timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("wger", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "wger",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_exercise(data: dict[str, object]) -> Exercise:
        try:
            ex_id = int(str(data.get("id", 0)))
        except (ValueError, TypeError):
            ex_id = 0

        name = str(data.get("name", ""))

        cat_raw = data.get("category", {})
        cat = cat_raw if isinstance(cat_raw, dict) else {}
        category = str(cat.get("name", ""))

        muscles_raw = data.get("muscles", [])
        muscles = muscles_raw if isinstance(muscles_raw, list) else []
        primary = tuple(
            str(m.get("name", "")) for m in muscles if isinstance(m, dict) and m.get("name")
        )

        sec_raw = data.get("muscles_secondary", [])
        secondary_list = sec_raw if isinstance(sec_raw, list) else []
        secondary = tuple(
            str(m.get("name", "")) for m in secondary_list if isinstance(m, dict) and m.get("name")
        )

        eq_raw = data.get("equipment", [])
        eq_list = eq_raw if isinstance(eq_raw, list) else []
        equipment = tuple(
            str(e.get("name", "")) for e in eq_list if isinstance(e, dict) and e.get("name")
        )

        desc_raw = str(data.get("description", ""))
        description = _HTML_TAG_RE.sub("", desc_raw).strip()

        return Exercise(
            id=ex_id,
            name=name,
            category=category,
            muscles_primary=primary,
            muscles_secondary=secondary,
            equipment=equipment,
            description=description,
        )

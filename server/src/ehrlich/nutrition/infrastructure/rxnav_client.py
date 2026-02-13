from __future__ import annotations

import asyncio
import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.nutrition.domain.entities import DrugInteraction
from ehrlich.nutrition.domain.repository import InteractionRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class RxNavClient(InteractionRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_interactions(
        self, substance: str, max_results: int = 10
    ) -> list[DrugInteraction]:
        rxcui = await self._resolve_rxcui(substance)
        if not rxcui:
            return []

        data = await self._get(
            f"{_BASE_URL}/interaction/interaction.json",
            params={"rxcui": rxcui},
        )

        interactions: list[DrugInteraction] = []
        groups_raw = data.get("interactionTypeGroup", [])
        groups = groups_raw if isinstance(groups_raw, list) else []
        for group in groups:
            if not isinstance(group, dict):
                continue
            for itype in group.get("interactionType", []):
                if not isinstance(itype, dict):
                    continue
                for pair in itype.get("interactionPair", []):
                    if not isinstance(pair, dict):
                        continue
                    interaction = self._parse_pair(pair, substance)
                    if interaction:
                        interactions.append(interaction)
                    if len(interactions) >= max_results:
                        return interactions
        return interactions

    async def _resolve_rxcui(self, substance: str) -> str | None:
        data = await self._get(
            f"{_BASE_URL}/rxcui.json",
            params={"name": substance},
        )
        id_group = data.get("idGroup", {})
        if not isinstance(id_group, dict):
            return None
        rxnorm_ids = id_group.get("rxnormId", [])
        if isinstance(rxnorm_ids, list) and rxnorm_ids:
            return str(rxnorm_ids[0])
        return None

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "RxNav rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("RxNav", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "RxNav timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("RxNav", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "RxNav",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_pair(pair: dict[str, object], query_substance: str) -> DrugInteraction | None:
        concepts = pair.get("interactionConcept", [])
        if not isinstance(concepts, list) or len(concepts) < 2:
            return None

        names: list[str] = []
        for concept in concepts[:2]:
            if not isinstance(concept, dict):
                return None
            source_concept = concept.get("sourceConceptItem", {})
            if not isinstance(source_concept, dict):
                return None
            name = str(source_concept.get("name", ""))
            if name:
                names.append(name)

        if len(names) < 2:
            return None

        description = str(pair.get("description", ""))
        severity = str(pair.get("severity", "N/A"))

        return DrugInteraction(
            drug_a=names[0],
            drug_b=names[1],
            severity=severity,
            description=description,
            source="RxNav",
        )

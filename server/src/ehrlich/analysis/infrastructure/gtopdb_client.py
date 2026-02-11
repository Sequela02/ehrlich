import asyncio
import logging

import httpx

from ehrlich.analysis.domain.pharmacology import PharmacologyEntry
from ehrlich.analysis.domain.repository import PharmacologyRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.guidetopharmacology.org/services"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_MAX_TARGETS = 3


class GtoPdbClient(PharmacologyRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, target: str, family: str = "") -> list[PharmacologyEntry]:
        target_ids = await self._search_targets(target, family)
        entries: list[PharmacologyEntry] = []
        for tid, tname, tfamily in target_ids[:_MAX_TARGETS]:
            interactions = await self._fetch_interactions(tid, tname, tfamily)
            entries.extend(interactions)
        return entries

    async def _search_targets(self, target: str, family: str) -> list[tuple[int, str, str]]:
        params: dict[str, str] = {"name": target}
        if family:
            params["type"] = family
        data = await self._execute_get(f"{_BASE_URL}/targets", params)
        if not isinstance(data, list):
            return []
        results: list[tuple[int, str, str]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            tid = item.get("targetId")
            if tid is None:
                continue
            tname = str(item.get("name", ""))
            tfamily = str(item.get("type", ""))
            results.append((int(tid), tname, tfamily))
        return results

    async def _fetch_interactions(
        self, target_id: int, target_name: str, target_family: str
    ) -> list[PharmacologyEntry]:
        url = f"{_BASE_URL}/targets/{target_id}/interactions"
        data = await self._execute_get(url, {})
        if not isinstance(data, list):
            return []
        entries: list[PharmacologyEntry] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            ligand = item.get("ligand", {})
            if not isinstance(ligand, dict):
                ligand = {}
            ligand_name = str(ligand.get("name", ""))
            ligand_smiles = str(ligand.get("smiles", "") or "")

            affinity_type = str(item.get("affinityParameter", "") or "")
            raw_value = item.get("affinity", "")
            try:
                affinity_value = float(raw_value) if raw_value else 0.0
            except (ValueError, TypeError):
                affinity_value = 0.0

            action = str(item.get("type", "") or "")
            approved = bool(ligand.get("approved", False))

            entries.append(
                PharmacologyEntry(
                    target_name=target_name,
                    target_family=target_family,
                    ligand_name=ligand_name,
                    ligand_smiles=ligand_smiles,
                    affinity_type=affinity_type,
                    affinity_value=affinity_value,
                    action=action,
                    approved=approved,
                )
            )
        return entries

    async def _execute_get(
        self, url: str, params: dict[str, str]
    ) -> list[object] | dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "GtoPdb rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("GtoPdb", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "GtoPdb timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("GtoPdb", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "GtoPdb", f"Request failed after {_MAX_RETRIES} attempts: {last_error}"
        )

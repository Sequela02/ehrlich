import asyncio
import logging
import re

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.domain.protein_target import ProteinTarget
from ehrlich.simulation.domain.repository import ProteinTargetRepository

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
_DATA_URL = "https://data.rcsb.org/rest/v1/core/entry"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class RCSBClient(ProteinTargetRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, query: str, organism: str = "", limit: int = 10) -> list[ProteinTarget]:
        search_query = self._build_query(query, organism, limit)
        result_ids = await self._execute_search(search_query)
        targets: list[ProteinTarget] = []
        for pdb_id in result_ids[:limit]:
            target = await self._fetch_entry(pdb_id)
            if target is not None:
                targets.append(target)
        return targets

    def _build_query(self, query: str, organism: str, limit: int) -> dict[str, object]:
        if organism:
            return {
                "query": {
                    "type": "group",
                    "logical_operator": "and",
                    "nodes": [
                        {
                            "type": "terminal",
                            "service": "full_text",
                            "parameters": {"value": query},
                        },
                        {
                            "type": "terminal",
                            "service": "text",
                            "parameters": {
                                "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
                                "operator": "contains_phrase",
                                "value": organism,
                            },
                        },
                    ],
                },
                "return_type": "entry",
                "request_options": {
                    "results_content_type": ["experimental"],
                    "paginate": {"start": 0, "rows": limit},
                },
            }
        return {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": query},
            },
            "return_type": "entry",
            "request_options": {
                "results_content_type": ["experimental"],
                "paginate": {"start": 0, "rows": limit},
            },
        }

    async def _execute_search(self, search_query: dict[str, object]) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(_SEARCH_URL, json=search_query)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "RCSB PDB rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("RCSB PDB", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                results = data.get("result_set", [])
                return [r["identifier"] for r in results if "identifier" in r]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "RCSB PDB timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("RCSB PDB", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "RCSB PDB", f"Search failed after {_MAX_RETRIES} attempts: {last_error}"
        )

    async def _fetch_entry(self, pdb_id: str) -> ProteinTarget | None:
        # Validate PDB ID format to prevent URL path injection
        if not re.match(r"^[0-9A-Za-z]{4}$", pdb_id):
            msg = f"Invalid PDB ID format: {pdb_id}"
            raise ValueError(msg)
        try:
            resp = await self._client.get(f"{_DATA_URL}/{pdb_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            struct = data.get("struct", {})
            name = str(struct.get("title", pdb_id))
            source = data.get("rcsb_entry_container_identifiers", {})
            organism = ""
            entity_src = data.get("polymer_entities", [])
            if entity_src:
                first = entity_src[0] if isinstance(entity_src, list) else None
                if first and isinstance(first, dict):
                    src_org = first.get("rcsb_entity_source_organism", [])
                    if src_org and isinstance(src_org, list) and src_org[0]:
                        organism = str(src_org[0].get("ncbi_scientific_name", ""))
            entry_id = str(source.get("entry_id", pdb_id))
            return ProteinTarget(
                pdb_id=entry_id.upper(),
                name=name[:100],
                organism=organism,
                center_x=0.0,
                center_y=0.0,
                center_z=0.0,
                box_size=22.0,
            )
        except httpx.HTTPError as e:
            logger.warning("Failed to fetch RCSB entry %s: %s", pdb_id, e)
            return None

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.domain.repository import TargetAssociationRepository
from ehrlich.simulation.domain.target_association import TargetAssociation

logger = logging.getLogger(__name__)

_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

_SEARCH_DISEASE_QUERY = """
query SearchDisease($q: String!) {
  search(queryString: $q, entityNames: ["disease"], page: {size: 1}) {
    hits {
      id
      name
    }
  }
}
"""

_ASSOCIATED_TARGETS_QUERY = """
query AssociatedTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    name
    associatedTargets(page: {size: $size}) {
      rows {
        target {
          id
          approvedName
          tractability {
            smallmolecule {
              topCategory
            }
          }
          knownDrugs {
            uniqueDrugs
          }
        }
        score
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""


class OpenTargetsClient(TargetAssociationRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, disease: str, limit: int = 10) -> list[TargetAssociation]:
        efo_id, disease_name = await self._resolve_disease(disease)
        if not efo_id:
            return []
        return await self._fetch_targets(efo_id, disease_name, limit)

    async def _resolve_disease(self, disease: str) -> tuple[str, str]:
        body: dict[str, Any] = {
            "query": _SEARCH_DISEASE_QUERY,
            "variables": {"q": disease},
        }
        data = await self._execute(body)
        top = data.get("data")
        if not isinstance(top, dict):
            return "", ""
        search = top.get("search")
        if not isinstance(search, dict):
            return "", ""
        hits = search.get("hits", [])
        if not isinstance(hits, list) or not hits:
            return "", ""
        hit = hits[0]
        if not isinstance(hit, dict):
            return "", ""
        return str(hit.get("id", "")), str(hit.get("name", disease))

    async def _fetch_targets(
        self, efo_id: str, disease_name: str, limit: int
    ) -> list[TargetAssociation]:
        body: dict[str, Any] = {
            "query": _ASSOCIATED_TARGETS_QUERY,
            "variables": {"efoId": efo_id, "size": limit},
        }
        data = await self._execute(body)
        top = data.get("data")
        if not isinstance(top, dict):
            return []
        disease_data = top.get("disease")
        if not isinstance(disease_data, dict) or not disease_data:
            return []
        assoc = disease_data.get("associatedTargets")
        if not isinstance(assoc, dict):
            return []
        rows = assoc.get("rows", [])
        if not isinstance(rows, list):
            return []
        associations: list[TargetAssociation] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = row.get("target", {})
            if not isinstance(target, dict):
                continue
            target_id = str(target.get("id", ""))
            target_name = str(target.get("approvedName", ""))

            # Tractability
            tractability = ""
            tract_data = target.get("tractability", {})
            if isinstance(tract_data, dict):
                sm = tract_data.get("smallmolecule", {})
                if isinstance(sm, dict):
                    tractability = str(sm.get("topCategory", ""))

            # Known drugs
            known_drugs: list[str] = []
            kd_data = target.get("knownDrugs", {})
            if isinstance(kd_data, dict):
                unique = kd_data.get("uniqueDrugs", 0)
                if unique and isinstance(unique, int) and unique > 0:
                    known_drugs = [f"{unique} known drug(s)"]

            # Evidence count from datatype scores
            evidence_count = 0
            dt_scores = row.get("datatypeScores", [])
            if isinstance(dt_scores, list):
                evidence_count = len(dt_scores)

            score = float(row.get("score", 0.0))

            associations.append(
                TargetAssociation(
                    target_id=target_id,
                    target_name=target_name,
                    disease_name=disease_name,
                    association_score=round(score, 4),
                    evidence_count=evidence_count,
                    tractability=tractability,
                    known_drugs=known_drugs,
                )
            )
        return associations

    async def _execute(self, body: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(_GRAPHQL_URL, json=body)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Open Targets rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("Open Targets", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "Open Targets timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("Open Targets", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "Open Targets",
            f"Search failed after {_MAX_RETRIES} attempts: {last_error}",
        )

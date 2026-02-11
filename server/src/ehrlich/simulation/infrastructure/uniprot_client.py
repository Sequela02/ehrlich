from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.domain.protein_annotation import ProteinAnnotation
from ehrlich.simulation.domain.repository import ProteinAnnotationRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://rest.uniprot.org/uniprotkb/search"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_FIELDS = "accession,protein_name,organism_name,cc_function,cc_disease,xref_pdb,xref_reactome,go"


class UniProtClient(ProteinAnnotationRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, query: str, organism: str = "", limit: int = 5
    ) -> list[ProteinAnnotation]:
        full_query = query
        if organism:
            full_query = f"{query} AND organism_name:{organism}"
        params = {
            "query": full_query,
            "fields": _FIELDS,
            "format": "json",
            "size": str(limit),
        }
        data = await self._execute(params)
        results = data.get("results", [])
        if not isinstance(results, list):
            return []
        return [self._parse_entry(entry) for entry in results]

    async def _execute(self, params: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(_BASE_URL, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "UniProt rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("UniProt", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "UniProt timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("UniProt", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "UniProt", f"Search failed after {_MAX_RETRIES} attempts: {last_error}"
        )

    def _parse_entry(self, entry: dict[str, Any]) -> ProteinAnnotation:
        accession = str(entry.get("primaryAccession", ""))

        # Protein name
        protein_name = entry.get("proteinDescription", {})
        rec_name = protein_name.get("recommendedName", {}) if isinstance(protein_name, dict) else {}
        full_name = rec_name.get("fullName", {}) if isinstance(rec_name, dict) else {}
        name = str(full_name.get("value", accession)) if isinstance(full_name, dict) else accession

        # Organism
        org_data = entry.get("organism", {})
        organism = str(org_data.get("scientificName", "")) if isinstance(org_data, dict) else ""

        # Function from comments
        function = ""
        disease_associations: list[str] = []
        comments = entry.get("comments", [])
        if isinstance(comments, list):
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                ctype = comment.get("commentType", "")
                if ctype == "FUNCTION":
                    texts = comment.get("texts", [])
                    if isinstance(texts, list) and texts:
                        first = texts[0]
                        if isinstance(first, dict):
                            function = str(first.get("value", ""))
                elif ctype == "DISEASE":
                    disease = comment.get("disease", {})
                    if isinstance(disease, dict):
                        dname = disease.get("diseaseId", "")
                        if dname:
                            disease_associations.append(str(dname))

        # GO terms
        go_terms: list[str] = []
        pdb_cross_refs: list[str] = []
        pathway = ""
        xrefs = entry.get("uniProtKBCrossReferences", [])
        if isinstance(xrefs, list):
            for xref in xrefs:
                if not isinstance(xref, dict):
                    continue
                db = xref.get("database", "")
                xid = str(xref.get("id", ""))
                if db == "GO":
                    props = xref.get("properties", [])
                    if isinstance(props, list):
                        for p in props:
                            if isinstance(p, dict) and p.get("key") == "GoTerm":
                                go_terms.append(str(p.get("value", xid)))
                                break
                        else:
                            go_terms.append(xid)
                elif db == "PDB":
                    pdb_cross_refs.append(xid)
                elif db == "Reactome" and not pathway:
                    props = xref.get("properties", [])
                    if isinstance(props, list):
                        for p in props:
                            if isinstance(p, dict) and p.get("key") == "PathwayName":
                                pathway = str(p.get("value", ""))
                                break

        return ProteinAnnotation(
            accession=accession,
            name=name,
            organism=organism,
            function=function,
            disease_associations=disease_associations,
            go_terms=go_terms,
            pdb_cross_refs=pdb_cross_refs,
            pathway=pathway,
        )

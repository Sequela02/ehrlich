import asyncio
import contextlib
import logging
from urllib.parse import quote

import httpx

from ehrlich.analysis.domain.compound import CompoundSearchResult
from ehrlich.analysis.domain.repository import CompoundSearchRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class PubChemClient(CompoundSearchRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, query: str, limit: int = 10) -> list[CompoundSearchResult]:
        encoded = quote(query, safe="")
        url = f"{_BASE_URL}/compound/name/{encoded}/JSON"
        data = await self._request_with_retry(url)
        return self._parse_compounds(data, limit)

    async def search_by_similarity(
        self, smiles: str, threshold: float = 0.8, limit: int = 10
    ) -> list[CompoundSearchResult]:
        encoded = quote(smiles, safe="")
        threshold_int = int(threshold * 100)
        url = (
            f"{_BASE_URL}/compound/fastsimilarity_2d/smiles/{encoded}/JSON"
            f"?Threshold={threshold_int}&MaxRecords={limit}"
        )
        data = await self._request_with_retry(url)
        return self._parse_compounds(data, limit)

    async def _request_with_retry(self, url: str) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url)
                if resp.status_code == 404:
                    return {}
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "PubChem rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("PubChem", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "PubChem timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("PubChem", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError("PubChem", f"Failed after {_MAX_RETRIES} attempts: {last_error}")

    @staticmethod
    def _parse_compounds(data: dict[str, object], limit: int) -> list[CompoundSearchResult]:
        if not data:
            return []
        compounds_raw = data.get("PC_Compounds", [])
        if not isinstance(compounds_raw, list):
            return []
        results: list[CompoundSearchResult] = []
        for compound in compounds_raw[:limit]:
            if not isinstance(compound, dict):
                continue
            cid = compound.get("id", {})
            if isinstance(cid, dict):
                cid = cid.get("id", {})
                if isinstance(cid, dict):
                    cid = cid.get("cid", 0)
            props = compound.get("props", [])
            smiles = ""
            iupac_name = ""
            molecular_formula = ""
            molecular_weight = 0.0
            if isinstance(props, list):
                for prop in props:
                    if not isinstance(prop, dict):
                        continue
                    urn = prop.get("urn", {})
                    if not isinstance(urn, dict):
                        continue
                    label = str(urn.get("label", ""))
                    name = str(urn.get("name", ""))
                    value = prop.get("value", {})
                    if not isinstance(value, dict):
                        continue
                    if label == "SMILES" and name == "Canonical":
                        smiles = str(value.get("sval", ""))
                    elif label == "IUPAC Name" and name == "Preferred":
                        iupac_name = str(value.get("sval", ""))
                    elif label == "Molecular Formula":
                        molecular_formula = str(value.get("sval", ""))
                    elif label == "Molecular Weight":
                        with contextlib.suppress(ValueError, TypeError):
                            molecular_weight = float(str(value.get("sval", "0")))
            if smiles and int(str(cid)) > 0:
                results.append(
                    CompoundSearchResult(
                        cid=int(str(cid)),
                        smiles=smiles,
                        iupac_name=iupac_name,
                        molecular_formula=molecular_formula,
                        molecular_weight=molecular_weight,
                    )
                )
        return results

import asyncio
import logging
import urllib.parse

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.domain.repository import ToxicityRepository
from ehrlich.simulation.domain.toxicity_profile import ToxicityProfile

logger = logging.getLogger(__name__)

_BASE_URL = "https://api-ccte.epa.gov"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class CompToxClient(ToxicityRepository):
    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key
        headers: dict[str, str] = {}
        if api_key:
            headers["x-api-key"] = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers=headers,
            timeout=_TIMEOUT,
        )

    async def fetch(self, identifier: str) -> ToxicityProfile | None:
        if not self._api_key:
            logger.info("CompTox API key not configured, skipping toxicity lookup")
            return None
        dtxsid = await self._resolve_dtxsid(identifier)
        if not dtxsid:
            return None
        return await self._fetch_hazard(dtxsid, identifier)

    async def _resolve_dtxsid(self, name: str) -> str | None:
        last_error: Exception | None = None
        encoded_name = urllib.parse.quote(name, safe="")
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(f"/chemical/search/by-name/{encoded_name}")
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "CompTox rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("EPA CompTox", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and data:
                    first = data[0]
                    if isinstance(first, dict):
                        return str(first.get("dtxsid", ""))
                elif isinstance(data, dict):
                    return str(data.get("dtxsid", ""))
                return None
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "CompTox timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("EPA CompTox", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "EPA CompTox",
            f"Chemical search failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    async def _fetch_hazard(self, dtxsid: str, name: str) -> ToxicityProfile | None:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(f"/hazard/search/by-dtxsid/{dtxsid}")
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "CompTox hazard rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("EPA CompTox", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                return self._parse_hazard(data, dtxsid, name)
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "CompTox hazard timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("EPA CompTox", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "EPA CompTox",
            f"Hazard lookup failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_hazard(data: object, dtxsid: str, name: str) -> ToxicityProfile:
        oral_ld50: float | None = None
        lc50_fish: float | None = None
        bcf: float | None = None
        dev_tox: bool | None = None
        mutagenicity: bool | None = None
        casrn = ""
        mw = 0.0

        records: list[dict[str, object]] = []
        if isinstance(data, list):
            records = [r for r in data if isinstance(r, dict)]
        elif isinstance(data, dict):
            records = [data]

        for record in records:
            casrn = casrn or str(record.get("casrn", ""))
            mw = mw or float(str(record.get("molecularWeight", 0) or 0))
            endpoint = str(record.get("endpointCategory", ""))
            value_str = str(record.get("toxvalNumeric", "") or "")
            try:
                value = float(value_str) if value_str else None
            except (ValueError, TypeError):
                value = None
            if endpoint == "acute oral" and value is not None and oral_ld50 is None:
                oral_ld50 = value
            elif endpoint == "acute aquatic" and value is not None and lc50_fish is None:
                lc50_fish = value
            elif endpoint == "bioconcentration" and value is not None and bcf is None:
                bcf = value
            elif endpoint == "developmental" and dev_tox is None:
                dev_tox = str(record.get("toxvalType", "")).lower() == "positive"
            elif endpoint == "mutagenicity" and mutagenicity is None:
                mutagenicity = str(record.get("toxvalType", "")).lower() == "positive"

        return ToxicityProfile(
            dtxsid=dtxsid,
            name=name,
            casrn=casrn,
            molecular_weight=mw,
            oral_rat_ld50=oral_ld50,
            lc50_fish=lc50_fish,
            bioconcentration_factor=bcf,
            developmental_toxicity=dev_tox,
            mutagenicity=mutagenicity,
        )

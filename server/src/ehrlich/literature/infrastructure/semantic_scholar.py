import asyncio
import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.repository import PaperSearchRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,authors,year,abstract,externalIds,citationCount"
_TIMEOUT = 15.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class SemanticScholarClient(PaperSearchRepository):
    def __init__(self, api_key: str | None = None) -> None:
        headers: dict[str, str] = {}
        if api_key:
            headers["x-api-key"] = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers=headers,
            timeout=_TIMEOUT,
        )

    async def search(self, query: str, limit: int = 10) -> list[Paper]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(
                    "/paper/search",
                    params={"query": query, "limit": min(limit, 100), "fields": _FIELDS},
                )
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "SemanticScholar rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                return [self._to_paper(item) for item in (data.get("data") or [])]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "SemanticScholar timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "SemanticScholar", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "SemanticScholar", f"Failed after {_MAX_RETRIES} attempts: {last_error}"
        )

    async def get_by_doi(self, doi: str) -> Paper | None:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(
                    f"/paper/DOI:{doi}",
                    params={"fields": _FIELDS},
                )
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "SemanticScholar rate limited on DOI (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
                resp.raise_for_status()
                return self._to_paper(resp.json())
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "SemanticScholar DOI timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "SemanticScholar", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "SemanticScholar", f"DOI lookup failed after {_MAX_RETRIES} attempts: {last_error}"
        )

    async def get_references(self, paper_id: str, limit: int = 10) -> list[Paper]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(
                    f"/paper/{paper_id}/references",
                    params={"fields": _FIELDS, "limit": min(limit, 100)},
                )
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "SemanticScholar refs rate limited (%d/%d), retry in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                papers = []
                for item in data.get("data") or []:
                    cited = item.get("citedPaper")
                    if cited and cited.get("title"):
                        papers.append(self._to_paper(cited))
                return papers
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "SemanticScholar references timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "SemanticScholar", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "SemanticScholar",
            f"References lookup failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    async def get_citing(self, paper_id: str, limit: int = 10) -> list[Paper]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(
                    f"/paper/{paper_id}/citations",
                    params={"fields": _FIELDS, "limit": min(limit, 100)},
                )
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "SemanticScholar cites rate limited (%d/%d), retry in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                papers = []
                for item in data.get("data") or []:
                    citing = item.get("citingPaper")
                    if citing and citing.get("title"):
                        papers.append(self._to_paper(citing))
                return papers
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "SemanticScholar citations timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "SemanticScholar", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "SemanticScholar",
            f"Citations lookup failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _to_paper(data: dict[str, object]) -> Paper:
        authors_raw = data.get("authors", [])
        authors = []
        if isinstance(authors_raw, list):
            for a in authors_raw:
                if isinstance(a, dict):
                    authors.append(str(a.get("name", "Unknown")))
                else:
                    authors.append(str(a))
        external_ids = data.get("externalIds") or {}
        doi = ""
        if isinstance(external_ids, dict):
            doi = str(external_ids.get("DOI", ""))
        return Paper(
            title=str(data.get("title", "")),
            authors=authors,
            year=int(str(data.get("year", 0) or 0)),
            abstract=str(data.get("abstract", "") or ""),
            doi=doi,
            citations=int(str(data.get("citationCount", 0) or 0)),
            source="semantic_scholar",
        )

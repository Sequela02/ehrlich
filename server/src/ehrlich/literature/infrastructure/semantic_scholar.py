import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.repository import PaperSearchRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,authors,year,abstract,externalIds,citationCount"
_TIMEOUT = 15.0


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
        try:
            resp = await self._client.get(
                "/paper/search",
                params={"query": query, "limit": min(limit, 100), "fields": _FIELDS},
            )
            if resp.status_code == 429:
                raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
            return [self._to_paper(item) for item in data.get("data", [])]
        except httpx.TimeoutException as e:
            raise ExternalServiceError("SemanticScholar", f"Timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError("SemanticScholar", f"HTTP {e.response.status_code}") from e

    async def get_by_doi(self, doi: str) -> Paper | None:
        try:
            resp = await self._client.get(
                f"/paper/DOI:{doi}",
                params={"fields": _FIELDS},
            )
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                raise ExternalServiceError("SemanticScholar", "Rate limit exceeded")
            resp.raise_for_status()
            return self._to_paper(resp.json())
        except httpx.TimeoutException as e:
            raise ExternalServiceError("SemanticScholar", f"Timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError("SemanticScholar", f"HTTP {e.response.status_code}") from e

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

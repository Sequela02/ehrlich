import logging

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.reference_set import CoreReferenceSet
from ehrlich.literature.domain.repository import PaperSearchRepository

logger = logging.getLogger(__name__)


class LiteratureService:
    def __init__(
        self,
        primary: PaperSearchRepository,
        fallback: PaperSearchRepository | None = None,
        references: CoreReferenceSet | None = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._references = references or CoreReferenceSet()

    async def search_papers(self, query: str, limit: int = 10) -> list[Paper]:
        try:
            return await self._primary.search(query, limit)
        except ExternalServiceError:
            logger.warning("Primary search failed, trying fallback")
            if self._fallback:
                return await self._fallback.search(query, limit)
            return []

    async def get_reference(self, key_or_doi: str) -> Paper | None:
        paper = self._references.find_by_key(key_or_doi)
        if paper:
            return paper
        paper = self._references.find_by_doi(key_or_doi)
        if paper:
            return paper
        try:
            return await self._primary.get_by_doi(key_or_doi)
        except ExternalServiceError:
            logger.warning("Primary DOI lookup failed, trying fallback")
            if self._fallback:
                return await self._fallback.get_by_doi(key_or_doi)
            return None

    def list_reference_keys(self) -> list[str]:
        return list(self._references._key_index.keys())

    @staticmethod
    def format_citation(paper: Paper) -> str:
        authors = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors += " et al."
        return f"{authors} ({paper.year}). {paper.title}. DOI: {paper.doi}"

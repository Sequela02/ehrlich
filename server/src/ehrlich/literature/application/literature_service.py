from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.repository import PaperSearchRepository


class LiteratureService:
    def __init__(self, repository: PaperSearchRepository) -> None:
        self._repository = repository

    async def search_papers(self, query: str, limit: int = 10) -> list[Paper]:
        return await self._repository.search(query, limit)

    async def get_reference(self, doi: str) -> Paper | None:
        return await self._repository.get_by_doi(doi)

    def format_citation(self, paper: Paper) -> str:
        authors = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors += " et al."
        return f"{authors} ({paper.year}). {paper.title}. DOI: {paper.doi}"

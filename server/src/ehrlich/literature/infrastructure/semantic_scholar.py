from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.repository import PaperSearchRepository


class SemanticScholarClient(PaperSearchRepository):
    async def search(self, query: str, limit: int = 10) -> list[Paper]:
        raise NotImplementedError

    async def get_by_doi(self, doi: str) -> Paper | None:
        raise NotImplementedError

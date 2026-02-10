from abc import ABC, abstractmethod

from ehrlich.literature.domain.paper import Paper


class PaperSearchRepository(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Paper]: ...

    @abstractmethod
    async def get_by_doi(self, doi: str) -> Paper | None: ...

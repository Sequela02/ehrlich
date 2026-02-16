from abc import ABC, abstractmethod

from ehrlich.literature.domain.paper import Paper


class PaperSearchRepository(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[Paper]: ...

    @abstractmethod
    async def get_by_doi(self, doi: str) -> Paper | None: ...

    @abstractmethod
    async def get_references(self, paper_id: str, limit: int = 5) -> list[Paper]: ...

    @abstractmethod
    async def get_citing(self, paper_id: str, limit: int = 5) -> list[Paper]: ...

import pytest

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.literature.application.literature_service import LiteratureService
from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.reference_set import CoreReferenceSet
from ehrlich.literature.domain.repository import PaperSearchRepository


class MockRepository(PaperSearchRepository):
    def __init__(self, papers: list[Paper] | None = None, fail: bool = False) -> None:
        self._papers = papers or []
        self._fail = fail

    async def search(self, query: str, limit: int = 10) -> list[Paper]:
        if self._fail:
            raise ExternalServiceError("Mock", "fail")
        return self._papers[:limit]

    async def get_by_doi(self, doi: str) -> Paper | None:
        if self._fail:
            raise ExternalServiceError("Mock", "fail")
        return next((p for p in self._papers if p.doi == doi), None)


def _make_paper(title: str = "Test", doi: str = "10.1234/test") -> Paper:
    return Paper(title=title, authors=["Author"], year=2024, abstract="Abstract", doi=doi)


class TestSearchPapers:
    @pytest.mark.asyncio
    async def test_primary_success(self) -> None:
        papers = [_make_paper()]
        service = LiteratureService(primary=MockRepository(papers))
        result = await service.search_papers("test")
        assert len(result) == 1
        assert result[0].title == "Test"

    @pytest.mark.asyncio
    async def test_primary_fails_uses_fallback(self) -> None:
        papers = [_make_paper("Fallback")]
        service = LiteratureService(
            primary=MockRepository(fail=True),
            fallback=MockRepository(papers),
        )
        result = await service.search_papers("test")
        assert len(result) == 1
        assert result[0].title == "Fallback"

    @pytest.mark.asyncio
    async def test_primary_fails_no_fallback(self) -> None:
        service = LiteratureService(primary=MockRepository(fail=True))
        result = await service.search_papers("test")
        assert result == []


class TestGetReference:
    @pytest.mark.asyncio
    async def test_by_key(self) -> None:
        paper = _make_paper("Halicin", "10.1038/halicin")
        refs = CoreReferenceSet(papers=(paper,), _key_index={"halicin": paper})
        service = LiteratureService(primary=MockRepository(), references=refs)
        result = await service.get_reference("halicin")
        assert result is not None
        assert result.title == "Halicin"

    @pytest.mark.asyncio
    async def test_by_doi(self) -> None:
        paper = _make_paper("Test", "10.1234/test")
        refs = CoreReferenceSet(papers=(paper,))
        service = LiteratureService(primary=MockRepository(), references=refs)
        result = await service.get_reference("10.1234/test")
        assert result is not None

    @pytest.mark.asyncio
    async def test_falls_through_to_primary(self) -> None:
        paper = _make_paper("Remote", "10.1234/remote")
        service = LiteratureService(primary=MockRepository([paper]))
        result = await service.get_reference("10.1234/remote")
        assert result is not None
        assert result.title == "Remote"


class TestFormatCitation:
    def test_basic(self) -> None:
        paper = _make_paper()
        citation = LiteratureService.format_citation(paper)
        assert "Author" in citation
        assert "2024" in citation
        assert "10.1234/test" in citation

    def test_many_authors_truncated(self) -> None:
        paper = Paper(title="T", authors=["A", "B", "C", "D"], year=2024, abstract="")
        citation = LiteratureService.format_citation(paper)
        assert "et al." in citation

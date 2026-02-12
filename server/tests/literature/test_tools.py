import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.literature import tools
from ehrlich.literature.domain.paper import Paper


def _mock_paper(title: str = "Mock Paper") -> Paper:
    return Paper(
        title=title,
        authors=["Smith, J."],
        year=2024,
        abstract="Test abstract for mock paper",
        doi="10.1234/mock",
        citations=10,
    )


class TestSearchLiterature:
    @pytest.mark.asyncio
    async def test_returns_papers(self) -> None:
        with patch.object(
            tools._service, "search_papers", new_callable=AsyncMock
        ) as mock:
            mock.return_value = [_mock_paper()]
            result = json.loads(await tools.search_literature("MRSA"))
            assert result["query"] == "MRSA"
            assert result["count"] == 1
            assert result["papers"][0]["title"] == "Mock Paper"
            assert result["papers"][0]["doi"] == "10.1234/mock"
            assert "citation" in result["papers"][0]

    @pytest.mark.asyncio
    async def test_empty_abstract_handled(self) -> None:
        paper = _mock_paper()
        paper = Paper(
            title="T", authors=[], year=2024, abstract="", doi="", citations=0
        )
        with patch.object(
            tools._service, "search_papers", new_callable=AsyncMock
        ) as mock:
            mock.return_value = [paper]
            result = json.loads(await tools.search_literature("test"))
            assert result["papers"][0]["abstract"] == ""


class TestSearchCitationsTool:
    @pytest.mark.asyncio
    async def test_returns_results(self) -> None:
        with patch.object(
            tools._service, "search_citations", new_callable=AsyncMock
        ) as mock:
            mock.return_value = [_mock_paper("Cited")]
            result = json.loads(
                await tools.search_citations("10.1234/test", direction="references")
            )
            assert result["paper_id"] == "10.1234/test"
            assert result["direction"] == "references"
            assert result["count"] == 1
            assert result["papers"][0]["title"] == "Cited"


class TestGetReference:
    @pytest.mark.asyncio
    async def test_known_key(self) -> None:
        result = json.loads(await tools.get_reference("halicin"))
        assert result["title"] == "A Deep Learning Approach to Antibiotic Discovery"
        assert result["year"] == 2020
        assert "citation" in result

    @pytest.mark.asyncio
    async def test_unknown_key(self) -> None:
        result = json.loads(await tools.get_reference("nonexistent_key"))
        assert "error" in result
        assert "available_keys" in result

    @pytest.mark.asyncio
    async def test_all_reference_keys(self) -> None:
        for key in ["halicin", "abaucin", "chemprop", "pkcsm", "who_bppl_2024", "amr_crisis"]:
            result = json.loads(await tools.get_reference(key))
            assert "title" in result, f"Key {key} not found"
            assert "error" not in result, f"Key {key} returned error"

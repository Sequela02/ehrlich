import json
from unittest.mock import AsyncMock

import pytest

from ehrlich.investigation.application.tool_cache import ToolCache
from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.investigation import Investigation


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()

    async def mock_search_literature(query: str, limit: int = 5) -> str:
        papers = [
            {
                "title": "Paper A",
                "authors": ["Author 1"],
                "year": 2024,
                "doi": "10.1234/a",
                "abstract": "Abstract A",
                "citations": 10,
            },
            {
                "title": "Paper B",
                "authors": ["Author 2"],
                "year": 2023,
                "doi": "10.1234/b",
                "abstract": "Abstract B",
                "citations": 5,
            },
            {
                "title": "Paper C",
                "authors": ["Author 3"],
                "year": 2022,
                "doi": "",
                "abstract": "Abstract C",
                "citations": 3,
            },
        ]
        return json.dumps({"query": query, "count": len(papers), "papers": papers})

    reg.register("search_literature", mock_search_literature, {"literature"})
    return reg


@pytest.fixture
def cache() -> ToolCache:
    return ToolCache()


@pytest.fixture
def dispatcher(registry: ToolRegistry, cache: ToolCache) -> ToolDispatcher:
    return ToolDispatcher(registry, cache, None, {})


@pytest.fixture
def investigation() -> Investigation:
    return AsyncMock(spec=Investigation)


class TestPaperDeduplication:
    @pytest.mark.asyncio
    async def test_first_call_returns_all_papers(
        self, dispatcher: ToolDispatcher, investigation: Investigation
    ) -> None:
        result_str = await dispatcher.dispatch(
            "search_literature", {"query": "antibiotics", "limit": 5}, investigation
        )
        result = json.loads(result_str)
        assert result["count"] == 3
        assert len(result["papers"]) == 3

    @pytest.mark.asyncio
    async def test_second_call_deduplicates_by_doi(
        self, dispatcher: ToolDispatcher, investigation: Investigation
    ) -> None:
        await dispatcher.dispatch(
            "search_literature", {"query": "antibiotics", "limit": 5}, investigation
        )

        result_str = await dispatcher.dispatch(
            "search_literature", {"query": "antimicrobials", "limit": 5}, investigation
        )
        result = json.loads(result_str)

        assert result["count"] == 0
        assert len(result["papers"]) == 0

    @pytest.mark.asyncio
    async def test_deduplicates_by_title_year_when_no_doi(
        self, registry: ToolRegistry, cache: ToolCache, investigation: Investigation
    ) -> None:
        async def mock_search_no_doi(query: str, limit: int = 5) -> str:
            papers = [
                {
                    "title": "Unique Paper",
                    "authors": ["Author"],
                    "year": 2024,
                    "doi": "",
                    "abstract": "Abstract",
                    "citations": 1,
                }
            ]
            return json.dumps({"query": query, "count": len(papers), "papers": papers})

        registry.register("search_literature", mock_search_no_doi, {"literature"})
        dispatcher = ToolDispatcher(registry, cache, None, {})

        result1_str = await dispatcher.dispatch(
            "search_literature", {"query": "query1", "limit": 5}, investigation
        )
        result1 = json.loads(result1_str)
        assert result1["count"] == 1

        result2_str = await dispatcher.dispatch(
            "search_literature", {"query": "query2", "limit": 5}, investigation
        )
        result2 = json.loads(result2_str)
        assert result2["count"] == 0

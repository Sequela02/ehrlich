from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.infrastructure.sqlite_repository import SqliteInvestigationRepository


@pytest.fixture
async def repository(tmp_path: Path) -> SqliteInvestigationRepository:
    db_path = str(tmp_path / "test.db")
    repo = SqliteInvestigationRepository(db_path)
    await repo.initialize()
    return repo


class TestSave:
    @pytest.mark.asyncio
    async def test_save_and_retrieve(self, repository: SqliteInvestigationRepository) -> None:
        inv = Investigation(prompt="Find antimicrobials for MRSA")
        await repository.save(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert retrieved.id == inv.id
        assert retrieved.prompt == "Find antimicrobials for MRSA"
        assert retrieved.status == InvestigationStatus.PENDING

    @pytest.mark.asyncio
    async def test_save_preserves_created_at(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert retrieved.created_at.tzinfo is not None
        delta = abs((retrieved.created_at - inv.created_at).total_seconds())
        assert delta < 1


class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_none_for_missing(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        result = await repository.get_by_id("nonexistent")
        assert result is None


class TestListAll:
    @pytest.mark.asyncio
    async def test_empty_list(self, repository: SqliteInvestigationRepository) -> None:
        result = await repository.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_ordered(self, repository: SqliteInvestigationRepository) -> None:
        inv1 = Investigation(
            prompt="First",
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        inv2 = Investigation(
            prompt="Second",
            created_at=datetime(2025, 1, 2, tzinfo=UTC),
        )
        await repository.save(inv1)
        await repository.save(inv2)

        result = await repository.list_all()
        assert len(result) == 2
        # Most recent first
        assert result[0].prompt == "Second"
        assert result[1].prompt == "First"


class TestUpdate:
    @pytest.mark.asyncio
    async def test_update_status(self, repository: SqliteInvestigationRepository) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        inv.status = InvestigationStatus.COMPLETED
        inv.summary = "Found 3 candidates"
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert retrieved.status == InvestigationStatus.COMPLETED
        assert retrieved.summary == "Found 3 candidates"

    @pytest.mark.asyncio
    async def test_update_findings_and_candidates(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        inv.record_finding(
            Finding(title="Key insight", detail="Details", phase="Literature Review")
        )
        inv.set_candidates(
            [
                Candidate(
                    smiles="CC(=O)Oc1ccccc1C(=O)O",
                    name="Aspirin",
                    rank=1,
                    notes="Good candidate",
                )
            ],
            ["10.1234/test"],
        )
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert len(retrieved.findings) == 1
        assert retrieved.findings[0].title == "Key insight"
        assert len(retrieved.candidates) == 1
        assert retrieved.candidates[0].smiles == "CC(=O)Oc1ccccc1C(=O)O"
        assert retrieved.citations == ["10.1234/test"]

    @pytest.mark.asyncio
    async def test_update_cost_data(self, repository: SqliteInvestigationRepository) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        inv.cost_data = {"total_cost_usd": 3.5, "input_tokens": 100000}
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert retrieved.cost_data["total_cost_usd"] == 3.5

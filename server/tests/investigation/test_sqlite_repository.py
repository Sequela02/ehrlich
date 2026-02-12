from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.experiment import Experiment
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
            Finding(
                title="Key insight",
                detail="Details",
                hypothesis_id="h1",
                evidence_type="supporting",
            )
        )
        inv.set_candidates(
            [
                Candidate(
                    identifier="CC(=O)Oc1ccccc1C(=O)O",
                    identifier_type="smiles",
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
        assert retrieved.candidates[0].identifier == "CC(=O)Oc1ccccc1C(=O)O"
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


class TestEvents:
    @pytest.mark.asyncio
    async def test_save_and_get_events(self, repository: SqliteInvestigationRepository) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        await repository.save_event(inv.id, "tool_called", '{"event":"tool_called","data":{}}')
        await repository.save_event(inv.id, "tool_result", '{"event":"tool_result","data":{}}')

        events = await repository.get_events(inv.id)
        assert len(events) == 2
        assert events[0]["event_type"] == "tool_called"
        assert events[1]["event_type"] == "tool_result"

    @pytest.mark.asyncio
    async def test_events_ordered_by_insertion(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        for i in range(5):
            await repository.save_event(inv.id, f"event_{i}", f'{{"n":{i}}}')

        events = await repository.get_events(inv.id)
        assert len(events) == 5
        for i, ev in enumerate(events):
            assert ev["event_type"] == f"event_{i}"

    @pytest.mark.asyncio
    async def test_events_filtered_by_investigation_id(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv1 = Investigation(prompt="First")
        inv2 = Investigation(prompt="Second")
        await repository.save(inv1)
        await repository.save(inv2)

        await repository.save_event(inv1.id, "tool_called", '{"data":"a"}')
        await repository.save_event(inv2.id, "tool_called", '{"data":"b"}')
        await repository.save_event(inv1.id, "thinking", '{"data":"c"}')

        events1 = await repository.get_events(inv1.id)
        events2 = await repository.get_events(inv2.id)
        assert len(events1) == 2
        assert len(events2) == 1

    @pytest.mark.asyncio
    async def test_get_events_empty(self, repository: SqliteInvestigationRepository) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)
        events = await repository.get_events(inv.id)
        assert events == []


class TestExperimentProtocolRoundtrip:
    @pytest.mark.asyncio
    async def test_experiment_protocol_fields_persist(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        exp = Experiment(
            hypothesis_id="h1",
            description="Test DBO inhibition",
            tool_plan=["search_bioactivity", "train_model"],
            independent_variable="C2 substituent pattern",
            dependent_variable="Ki (nM)",
            controls=["positive: Avibactam", "negative: Aspirin"],
            confounders=["Dataset bias", "Scoring function limits"],
            analysis_plan="AUC >0.7, docking <-7 kcal/mol",
            success_criteria=">=3 candidates meet thresholds",
            failure_criteria="<2 compounds or AUC <0.7",
        )
        inv.add_experiment(exp)
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert len(retrieved.experiments) == 1
        e = retrieved.experiments[0]
        assert e.independent_variable == "C2 substituent pattern"
        assert e.dependent_variable == "Ki (nM)"
        assert e.controls == ["positive: Avibactam", "negative: Aspirin"]
        assert e.confounders == ["Dataset bias", "Scoring function limits"]
        assert e.analysis_plan == "AUC >0.7, docking <-7 kcal/mol"
        assert e.success_criteria == ">=3 candidates meet thresholds"
        assert e.failure_criteria == "<2 compounds or AUC <0.7"

    @pytest.mark.asyncio
    async def test_experiment_protocol_defaults_on_missing(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        exp = Experiment(hypothesis_id="h1", description="Minimal experiment")
        inv.add_experiment(exp)
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        e = retrieved.experiments[0]
        assert e.independent_variable == ""
        assert e.dependent_variable == ""
        assert e.controls == []
        assert e.confounders == []
        assert e.analysis_plan == ""
        assert e.success_criteria == ""
        assert e.failure_criteria == ""


class TestEvidenceLevelRoundtrip:
    @pytest.mark.asyncio
    async def test_finding_evidence_level_persists(
        self, repository: SqliteInvestigationRepository
    ) -> None:
        inv = Investigation(prompt="Test")
        await repository.save(inv)

        inv.record_finding(
            Finding(
                title="Systematic review",
                detail="Meta-analysis shows pooled effect",
                hypothesis_id="h1",
                evidence_type="supporting",
                evidence_level=1,
            )
        )
        inv.record_finding(
            Finding(
                title="Case series",
                detail="5 patients observed",
                hypothesis_id="h1",
                evidence_type="neutral",
                evidence_level=5,
            )
        )
        inv.record_finding(
            Finding(
                title="Unrated finding",
                detail="No level assigned",
                evidence_level=0,
            )
        )
        await repository.update(inv)

        retrieved = await repository.get_by_id(inv.id)
        assert retrieved is not None
        assert len(retrieved.findings) == 3
        assert retrieved.findings[0].evidence_level == 1
        assert retrieved.findings[1].evidence_level == 5
        assert retrieved.findings[2].evidence_level == 0

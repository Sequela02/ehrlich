"""Tests for InvestigationRepository against a real PostgreSQL instance."""

from __future__ import annotations

import contextlib
import json
import os
import uuid

import asyncpg
import pytest

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.experiment import Experiment
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.hypothesis import Hypothesis
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.infrastructure.repository import InvestigationRepository

_TEST_DATABASE_URL = os.environ.get(
    "EHRLICH_TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ehrlich_test",
)


@pytest.fixture
async def repo() -> InvestigationRepository:
    # Ensure test database exists
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    with contextlib.suppress(asyncpg.DuplicateDatabaseError):
        await conn.execute("CREATE DATABASE ehrlich_test")
    await conn.close()

    repository = InvestigationRepository(_TEST_DATABASE_URL)
    await repository.initialize()

    # Clean tables between tests
    pool = repository._get_pool()
    async with pool.acquire() as c:
        await c.execute("DELETE FROM events")
        await c.execute("DELETE FROM credit_transactions")
        await c.execute("DELETE FROM investigations")
        await c.execute("DELETE FROM users")

    yield repository  # type: ignore[misc]
    await repository.close()


def _make_investigation(
    prompt: str = "Test investigation",
    investigation_id: str | None = None,
) -> Investigation:
    return Investigation(
        prompt=prompt,
        id=investigation_id or str(uuid.uuid4()),
    )


def _make_hypothesis(
    statement: str = "Test hypothesis",
    hypothesis_id: str | None = None,
) -> Hypothesis:
    return Hypothesis(
        statement=statement,
        rationale="Test rationale",
        id=hypothesis_id or str(uuid.uuid4())[:8],
        prediction="Expect result X",
        null_prediction="No effect",
        success_criteria="p < 0.05",
        failure_criteria="p > 0.05",
        scope="in vitro",
        hypothesis_type="mechanistic",
        prior_confidence=0.6,
    )


def _make_finding(hypothesis_id: str = "") -> Finding:
    return Finding(
        title="Test finding",
        detail="Some detail about the finding",
        evidence="Strong evidence from ChEMBL",
        hypothesis_id=hypothesis_id,
        evidence_type="supporting",
        confidence=0.85,
        source_type="chembl",
        source_id="CHEMBL12345",
        evidence_level=3,
    )


class TestSaveAndGetById:
    async def test_roundtrip_minimal(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        await repo.save(inv)

        loaded = await repo.get_by_id(inv.id)
        assert loaded is not None
        assert loaded.id == inv.id
        assert loaded.prompt == inv.prompt
        assert loaded.status == InvestigationStatus.PENDING

    async def test_roundtrip_with_entities(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        hyp = _make_hypothesis()
        inv.add_hypothesis(hyp)

        exp = Experiment(
            hypothesis_id=hyp.id,
            description="Run binding assay",
            tool_plan=["explore_dataset", "train_model"],
            independent_variable="compound concentration",
            dependent_variable="MIC value",
            controls=["vehicle control"],
            confounders=["temperature"],
            analysis_plan="Compare MIC distributions",
            success_criteria="MIC < 4 ug/mL",
            failure_criteria="MIC > 32 ug/mL",
        )
        inv.add_experiment(exp)

        finding = _make_finding(hypothesis_id=hyp.id)
        inv.record_finding(finding)

        candidate = Candidate(
            identifier="CCO",
            identifier_type="SMILES",
            name="Ethanol",
            rank=1,
            notes="Test candidate",
            scores={"binding": 0.92, "admet": 0.78},
            attributes={"mw": "46.07"},
        )
        inv.set_candidates([candidate], ["doi:10.1234/test"])

        nc = NegativeControl(
            identifier="O",
            identifier_type="SMILES",
            name="Water",
            score=0.05,
            threshold=0.5,
            expected_inactive=True,
            source="ChEMBL",
        )
        inv.add_negative_control(nc)
        inv.domain = "molecular"
        inv.cost_data = {"total_cost_usd": 0.05}

        await repo.save(inv)

        loaded = await repo.get_by_id(inv.id)
        assert loaded is not None

        # Hypotheses
        assert len(loaded.hypotheses) == 1
        h = loaded.hypotheses[0]
        assert h.id == hyp.id
        assert h.statement == hyp.statement
        assert h.rationale == "Test rationale"
        assert h.prediction == "Expect result X"
        assert h.null_prediction == "No effect"
        assert h.success_criteria == "p < 0.05"
        assert h.failure_criteria == "p > 0.05"
        assert h.scope == "in vitro"
        assert h.hypothesis_type == "mechanistic"
        assert h.prior_confidence == 0.6

        # Experiments
        assert len(loaded.experiments) == 1
        e = loaded.experiments[0]
        assert e.id == exp.id
        assert e.hypothesis_id == hyp.id
        assert e.description == "Run binding assay"
        assert e.tool_plan == ["explore_dataset", "train_model"]
        assert e.independent_variable == "compound concentration"
        assert e.dependent_variable == "MIC value"
        assert e.controls == ["vehicle control"]
        assert e.confounders == ["temperature"]
        assert e.analysis_plan == "Compare MIC distributions"
        assert e.success_criteria == "MIC < 4 ug/mL"

        # Findings
        assert len(loaded.findings) == 1
        f = loaded.findings[0]
        assert f.title == "Test finding"
        assert f.evidence_type == "supporting"
        assert f.source_type == "chembl"
        assert f.source_id == "CHEMBL12345"
        assert f.evidence_level == 3

        # Candidates
        assert len(loaded.candidates) == 1
        c = loaded.candidates[0]
        assert c.identifier == "CCO"
        assert c.scores["binding"] == 0.92
        assert c.attributes["mw"] == "46.07"

        # Negative controls
        assert len(loaded.negative_controls) == 1
        nc_loaded = loaded.negative_controls[0]
        assert nc_loaded.identifier == "O"
        assert nc_loaded.correctly_classified is True

        # Citations
        assert loaded.citations == ["doi:10.1234/test"]

        # Domain + cost
        assert loaded.domain == "molecular"
        assert loaded.cost_data == {"total_cost_usd": 0.05}

    async def test_get_nonexistent_returns_none(self, repo: InvestigationRepository) -> None:
        result = await repo.get_by_id("nonexistent-id")
        assert result is None

    async def test_save_with_user_id(self, repo: InvestigationRepository) -> None:
        user = await repo.get_or_create_user("workos_abc", "test@example.com")
        inv = _make_investigation()
        await repo.save(inv, user_id=str(user["id"]))

        loaded = await repo.get_by_id(inv.id)
        assert loaded is not None
        assert loaded.prompt == inv.prompt


class TestListAll:
    async def test_empty(self, repo: InvestigationRepository) -> None:
        result = await repo.list_all()
        assert result == []

    async def test_ordered_by_created_at_desc(self, repo: InvestigationRepository) -> None:
        import asyncio

        inv1 = _make_investigation(prompt="First")
        await repo.save(inv1)
        await asyncio.sleep(0.05)  # Ensure distinct timestamps
        inv2 = _make_investigation(prompt="Second")
        await repo.save(inv2)

        result = await repo.list_all()
        assert len(result) == 2
        assert result[0].prompt == "Second"
        assert result[1].prompt == "First"


class TestListByUser:
    async def test_filters_by_user(self, repo: InvestigationRepository) -> None:
        user_a = await repo.get_or_create_user("workos_a", "a@test.com")
        user_b = await repo.get_or_create_user("workos_b", "b@test.com")

        inv_a = _make_investigation(prompt="User A investigation")
        inv_b = _make_investigation(prompt="User B investigation")
        await repo.save(inv_a, user_id=str(user_a["id"]))
        await repo.save(inv_b, user_id=str(user_b["id"]))

        result = await repo.list_by_user(str(user_a["id"]))
        assert len(result) == 1
        assert result[0].prompt == "User A investigation"


class TestUpdate:
    async def test_modify_and_reread(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        await repo.save(inv)

        inv.status = InvestigationStatus.RUNNING
        inv.domain = "training"
        inv.iteration = 2
        hyp = _make_hypothesis()
        inv.add_hypothesis(hyp)
        await repo.update(inv)

        loaded = await repo.get_by_id(inv.id)
        assert loaded is not None
        assert loaded.status == InvestigationStatus.RUNNING
        assert loaded.domain == "training"
        assert loaded.iteration == 2
        assert len(loaded.hypotheses) == 1

    async def test_update_triggers_fts_on_completed(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation(prompt="antimicrobial resistance")
        hyp = _make_hypothesis(statement="Beta-lactam compounds inhibit PBP2a")
        inv.add_hypothesis(hyp)
        inv.record_finding(
            Finding(
                title="Ceftaroline binding to PBP2a",
                detail="Strong binding affinity observed in ChEMBL data",
                hypothesis_id=hyp.id,
                evidence_type="supporting",
                source_type="chembl",
                source_id="CHEMBL54321",
            )
        )
        await repo.save(inv)

        inv.status = InvestigationStatus.COMPLETED
        inv.summary = "Found effective compounds"
        await repo.update(inv)

        # FTS should now find this
        results = await repo.search_findings("ceftaroline binding")
        assert len(results) > 0
        assert results[0]["investigation_id"] == inv.id


class TestEvents:
    async def test_save_and_get_events(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        await repo.save(inv)

        event_data_1 = json.dumps({"hypothesis_id": "h1", "statement": "test"})
        event_data_2 = json.dumps({"tool_name": "validate_smiles"})
        await repo.save_event(inv.id, "hypothesis_formulated", event_data_1)
        await repo.save_event(inv.id, "tool_called", event_data_2)

        events = await repo.get_events(inv.id)
        assert len(events) == 2
        assert events[0]["event_type"] == "hypothesis_formulated"
        assert events[1]["event_type"] == "tool_called"

    async def test_events_ordered_by_id(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        await repo.save(inv)

        for i in range(5):
            await repo.save_event(inv.id, f"event_{i}", json.dumps({"i": i}))

        events = await repo.get_events(inv.id)
        assert len(events) == 5
        for i, ev in enumerate(events):
            assert ev["event_type"] == f"event_{i}"

    async def test_events_empty_for_nonexistent(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation()
        await repo.save(inv)
        events = await repo.get_events(inv.id)
        assert events == []


class TestSearchFindings:
    async def test_search_returns_matching_findings(self, repo: InvestigationRepository) -> None:
        inv = _make_investigation(prompt="Find MRSA compounds")
        hyp = _make_hypothesis(statement="Vancomycin analogs effective against MRSA")
        inv.add_hypothesis(hyp)
        inv.record_finding(
            Finding(
                title="Vancomycin derivative shows potent activity",
                detail="MIC of 0.5 ug/mL against MRSA strain USA300",
                hypothesis_id=hyp.id,
                evidence_type="supporting",
                source_type="chembl",
                source_id="CHEMBL99",
            )
        )
        await repo.save(inv)

        # Mark completed to trigger FTS rebuild
        inv.status = InvestigationStatus.COMPLETED
        await repo.update(inv)

        results = await repo.search_findings("vancomycin MRSA")
        assert len(results) >= 1
        hit = results[0]
        assert hit["investigation_id"] == inv.id
        assert hit["finding_title"] == "Vancomycin derivative shows potent activity"
        assert hit["evidence_type"] == "supporting"
        assert hit["source_type"] == "chembl"
        assert hit["hypothesis_statement"] == "Vancomycin analogs effective against MRSA"

    async def test_search_no_results(self, repo: InvestigationRepository) -> None:
        results = await repo.search_findings("xyzzyx_nonexistent_term")
        assert results == []

    async def test_search_respects_limit(self, repo: InvestigationRepository) -> None:
        # Create 3 investigations with matching findings
        for i in range(3):
            inv = _make_investigation(prompt=f"Penicillin research {i}")
            hyp = _make_hypothesis(statement=f"Penicillin variant {i} is effective")
            inv.add_hypothesis(hyp)
            inv.record_finding(
                Finding(
                    title=f"Penicillin result {i}",
                    detail="Penicillin binding observed",
                    hypothesis_id=hyp.id,
                    evidence_type="supporting",
                )
            )
            await repo.save(inv)
            inv.status = InvestigationStatus.COMPLETED
            await repo.update(inv)

        results = await repo.search_findings("penicillin", limit=2)
        assert len(results) <= 2


class TestGetOrCreateUser:
    async def test_creates_new_user(self, repo: InvestigationRepository) -> None:
        user = await repo.get_or_create_user("workos_new", "new@test.com")
        assert user["workos_id"] == "workos_new"
        assert user["email"] == "new@test.com"
        assert user["credits"] == 5  # default

    async def test_returns_existing_user(self, repo: InvestigationRepository) -> None:
        user1 = await repo.get_or_create_user("workos_exist", "exist@test.com")
        user2 = await repo.get_or_create_user("workos_exist", "exist@test.com")
        assert user1["id"] == user2["id"]
        assert user1["credits"] == user2["credits"]

    async def test_idempotent(self, repo: InvestigationRepository) -> None:
        for _ in range(3):
            user = await repo.get_or_create_user("workos_idem", "idem@test.com")
        assert user["workos_id"] == "workos_idem"


class TestGetUserCredits:
    async def test_default_credits(self, repo: InvestigationRepository) -> None:
        await repo.get_or_create_user("workos_cred", "cred@test.com")
        credits = await repo.get_user_credits("workos_cred")
        assert credits == 5

    async def test_nonexistent_user_returns_zero(self, repo: InvestigationRepository) -> None:
        credits = await repo.get_user_credits("workos_nonexist")
        assert credits == 0


class TestDeductCredits:
    async def test_successful_deduction(self, repo: InvestigationRepository) -> None:
        await repo.get_or_create_user("workos_ded", "ded@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        result = await repo.deduct_credits("workos_ded", 3, inv.id)
        assert result is True

        credits = await repo.get_user_credits("workos_ded")
        assert credits == 2

    async def test_insufficient_balance(self, repo: InvestigationRepository) -> None:
        await repo.get_or_create_user("workos_insuf", "insuf@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        result = await repo.deduct_credits("workos_insuf", 10, inv.id)
        assert result is False

        # Credits unchanged
        credits = await repo.get_user_credits("workos_insuf")
        assert credits == 5

    async def test_exact_balance_deduction(self, repo: InvestigationRepository) -> None:
        await repo.get_or_create_user("workos_exact", "exact@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        result = await repo.deduct_credits("workos_exact", 5, inv.id)
        assert result is True

        credits = await repo.get_user_credits("workos_exact")
        assert credits == 0

    async def test_records_transaction(self, repo: InvestigationRepository) -> None:
        user = await repo.get_or_create_user("workos_txn", "txn@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        await repo.deduct_credits("workos_txn", 2, inv.id)

        pool = repo._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM credit_transactions WHERE user_id = $1",
                user["id"],
            )
            assert len(rows) == 1
            assert rows[0]["amount"] == -2
            assert rows[0]["type"] == "deduction"
            assert rows[0]["investigation_id"] == inv.id


class TestRefundCredits:
    async def test_successful_refund(self, repo: InvestigationRepository) -> None:
        await repo.get_or_create_user("workos_ref", "ref@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        await repo.deduct_credits("workos_ref", 3, inv.id)
        assert await repo.get_user_credits("workos_ref") == 2

        await repo.refund_credits("workos_ref", 3, inv.id)
        assert await repo.get_user_credits("workos_ref") == 5

    async def test_records_refund_transaction(self, repo: InvestigationRepository) -> None:
        user = await repo.get_or_create_user("workos_reftx", "reftx@test.com")
        inv = _make_investigation()
        await repo.save(inv)

        await repo.deduct_credits("workos_reftx", 2, inv.id)
        await repo.refund_credits("workos_reftx", 2, inv.id)

        pool = repo._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM credit_transactions WHERE user_id = $1 ORDER BY id",
                user["id"],
            )
            assert len(rows) == 2
            assert rows[0]["type"] == "deduction"
            assert rows[0]["amount"] == -2
            assert rows[1]["type"] == "refund"
            assert rows[1]["amount"] == 2

    async def test_refund_nonexistent_user(self, repo: InvestigationRepository) -> None:
        # Should not raise -- just a no-op
        await repo.refund_credits("workos_nonexist", 5, "inv-id")


class TestPoolNotInitialized:
    async def test_get_pool_raises_before_init(self) -> None:
        repo = InvestigationRepository(_TEST_DATABASE_URL)
        with pytest.raises(RuntimeError, match="PostgreSQL pool not initialized"):
            repo._get_pool()

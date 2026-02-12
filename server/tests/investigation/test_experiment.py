import pytest

from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus


class TestExperimentCreation:
    def test_minimal_creation(self) -> None:
        exp = Experiment(hypothesis_id="h1", description="Test binding")
        assert exp.hypothesis_id == "h1"
        assert exp.description == "Test binding"
        assert exp.status == ExperimentStatus.PLANNED
        assert len(exp.id) == 8

    def test_protocol_fields_default_empty(self) -> None:
        exp = Experiment(hypothesis_id="h1", description="Test")
        assert exp.independent_variable == ""
        assert exp.dependent_variable == ""
        assert exp.controls == []
        assert exp.confounders == []
        assert exp.analysis_plan == ""
        assert exp.success_criteria == ""
        assert exp.failure_criteria == ""

    def test_protocol_fields_populated(self) -> None:
        exp = Experiment(
            hypothesis_id="h1",
            description="Test DBO inhibition",
            independent_variable="C2 substituent pattern",
            dependent_variable="Ki (nM)",
            controls=["positive: Avibactam", "negative: Aspirin"],
            confounders=["Dataset bias", "Scoring function limits"],
            analysis_plan="AUC >0.7, docking <-7 kcal/mol",
            success_criteria=">=3 candidates meet thresholds",
            failure_criteria="<2 compounds or AUC <0.7",
        )
        assert exp.independent_variable == "C2 substituent pattern"
        assert exp.dependent_variable == "Ki (nM)"
        assert len(exp.controls) == 2
        assert "positive: Avibactam" in exp.controls
        assert len(exp.confounders) == 2
        assert exp.analysis_plan == "AUC >0.7, docking <-7 kcal/mol"
        assert exp.success_criteria == ">=3 candidates meet thresholds"
        assert exp.failure_criteria == "<2 compounds or AUC <0.7"

    def test_requires_hypothesis_id(self) -> None:
        with pytest.raises(ValueError, match="hypothesis"):
            Experiment(hypothesis_id="", description="Test")

    def test_requires_description(self) -> None:
        with pytest.raises(ValueError, match="description"):
            Experiment(hypothesis_id="h1", description="")

    def test_with_tool_plan(self) -> None:
        exp = Experiment(
            hypothesis_id="h1",
            description="Test",
            tool_plan=["search_bioactivity", "train_model"],
        )
        assert exp.tool_plan == ["search_bioactivity", "train_model"]

    def test_controls_are_independent_lists(self) -> None:
        exp1 = Experiment(hypothesis_id="h1", description="A")
        exp2 = Experiment(hypothesis_id="h2", description="B")
        exp1.controls.append("positive: X")
        assert exp2.controls == []

    def test_confounders_are_independent_lists(self) -> None:
        exp1 = Experiment(hypothesis_id="h1", description="A")
        exp2 = Experiment(hypothesis_id="h2", description="B")
        exp1.confounders.append("bias")
        assert exp2.confounders == []

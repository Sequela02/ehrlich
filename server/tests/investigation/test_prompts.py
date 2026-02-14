from ehrlich.investigation.application.multi_orchestrator import SEARCH_TOOLS
from ehrlich.investigation.application.prompts.builders import (
    build_literature_assessment_prompt,
    build_literature_survey_prompt,
    build_pico_and_classification_prompt,
    build_researcher_prompt,
)
from ehrlich.investigation.application.prompts.constants import (
    DIRECTOR_EVALUATION_PROMPT,
    DIRECTOR_EXPERIMENT_PROMPT,
    DIRECTOR_SYNTHESIS_PROMPT,
    RESEARCHER_EXPERIMENT_PROMPT,
)
from ehrlich.investigation.application.prompts.director import (
    build_experiment_prompt,
    build_synthesis_prompt,
)
from ehrlich.investigation.domain.domains.molecular import MOLECULAR_SCIENCE
from ehrlich.investigation.domain.domains.nutrition import NUTRITION_SCIENCE
from ehrlich.investigation.domain.domains.training import TRAINING_SCIENCE


class TestBuildPicoAndClassificationPrompt:
    def test_contains_categories(self) -> None:
        prompt = build_pico_and_classification_prompt()
        assert "antimicrobial" in prompt
        assert "oncology" in prompt
        assert "other" in prompt

    def test_custom_categories(self) -> None:
        cats = frozenset({"training", "nutrition"})
        prompt = build_pico_and_classification_prompt(cats)
        assert "training" in prompt
        assert "nutrition" in prompt
        assert "other" in prompt  # always added

    def test_output_format(self) -> None:
        prompt = build_pico_and_classification_prompt()
        assert '"domain"' in prompt
        assert '"population"' in prompt
        assert '"intervention"' in prompt
        assert '"comparison"' in prompt
        assert '"outcome"' in prompt
        assert '"search_terms"' in prompt


class TestBuildLiteratureSurveyPrompt:
    def test_includes_pico(self) -> None:
        pico = {
            "population": "MRSA strains",
            "intervention": "beta-lactamase inhibitors",
            "comparison": "existing treatments",
            "outcome": "MIC reduction",
            "search_terms": ["MRSA inhibitors", "beta-lactamase"],
        }
        prompt = build_literature_survey_prompt(None, pico)
        assert "MRSA strains" in prompt
        assert "beta-lactamase inhibitors" in prompt
        assert "MIC reduction" in prompt

    def test_includes_search_protocol(self) -> None:
        prompt = build_literature_survey_prompt(None, {})
        assert "search_citations" in prompt
        assert "Greenhalgh" in prompt
        assert "saturation" in prompt.lower()

    def test_includes_evidence_grading(self) -> None:
        prompt = build_literature_survey_prompt(None, {})
        assert "evidence_level" in prompt
        assert "Systematic review" in prompt


class TestBuildLiteratureAssessmentPrompt:
    def test_includes_grade_criteria(self) -> None:
        prompt = build_literature_assessment_prompt()
        assert "high" in prompt
        assert "moderate" in prompt
        assert "low" in prompt
        assert "very_low" in prompt

    def test_includes_amstar_domains(self) -> None:
        prompt = build_literature_assessment_prompt()
        assert "Protocol-guided search" in prompt
        assert "Multi-source search" in prompt
        assert "Evidence quality" in prompt

    def test_output_format(self) -> None:
        prompt = build_literature_assessment_prompt()
        assert '"evidence_grade"' in prompt
        assert '"reasoning"' in prompt
        assert '"assessment"' in prompt


class TestDirectorExperimentPrompt:
    def test_static_prompt_has_methodology(self) -> None:
        assert "VARIABLES" in DIRECTOR_EXPERIMENT_PROMPT
        assert "CONTROLS" in DIRECTOR_EXPERIMENT_PROMPT
        assert "CONFOUNDERS" in DIRECTOR_EXPERIMENT_PROMPT
        assert "ANALYSIS PLAN" in DIRECTOR_EXPERIMENT_PROMPT
        assert "SENSITIVITY" in DIRECTOR_EXPERIMENT_PROMPT

    def test_static_prompt_output_format(self) -> None:
        assert '"independent_variable"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"dependent_variable"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"controls"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"confounders"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"analysis_plan"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"success_criteria"' in DIRECTOR_EXPERIMENT_PROMPT
        assert '"failure_criteria"' in DIRECTOR_EXPERIMENT_PROMPT

    def test_static_prompt_no_expected_findings(self) -> None:
        assert "expected_findings" not in DIRECTOR_EXPERIMENT_PROMPT

    def test_domain_prompt_has_methodology(self) -> None:
        prompt = build_experiment_prompt(MOLECULAR_SCIENCE)
        assert "VARIABLES" in prompt
        assert "CONTROLS" in prompt
        assert "CONFOUNDERS" in prompt
        assert "ANALYSIS PLAN" in prompt
        assert "SENSITIVITY" in prompt

    def test_domain_prompt_output_format(self) -> None:
        prompt = build_experiment_prompt(MOLECULAR_SCIENCE)
        assert '"independent_variable"' in prompt
        assert '"dependent_variable"' in prompt
        assert '"controls"' in prompt
        assert '"analysis_plan"' in prompt

    def test_training_domain_prompt(self) -> None:
        prompt = build_experiment_prompt(TRAINING_SCIENCE)
        assert "VARIABLES" in prompt
        assert '"success_criteria"' in prompt


class TestResearcherExperimentPrompt:
    def test_static_prompt_has_methodology(self) -> None:
        assert "SENSITIVITY" in RESEARCHER_EXPERIMENT_PROMPT
        assert "APPLICABILITY DOMAIN" in RESEARCHER_EXPERIMENT_PROMPT
        assert "UNCERTAINTY" in RESEARCHER_EXPERIMENT_PROMPT
        assert "VERIFICATION" in RESEARCHER_EXPERIMENT_PROMPT
        assert "NEGATIVE RESULTS" in RESEARCHER_EXPERIMENT_PROMPT

    def test_domain_prompt_has_methodology(self) -> None:
        prompt = build_researcher_prompt(MOLECULAR_SCIENCE)
        assert "SENSITIVITY" in prompt
        assert "APPLICABILITY DOMAIN" in prompt
        assert "UNCERTAINTY" in prompt
        assert "VERIFICATION" in prompt
        assert "NEGATIVE RESULTS" in prompt

    def test_training_domain_prompt_has_methodology(self) -> None:
        prompt = build_researcher_prompt(TRAINING_SCIENCE)
        assert "SENSITIVITY" in prompt
        assert "NEGATIVE RESULTS" in prompt


class TestDirectorEvaluationPrompt:
    def test_has_methodology_checks(self) -> None:
        assert "methodology_checks" in DIRECTOR_EVALUATION_PROMPT
        assert "CONTROLS" in DIRECTOR_EVALUATION_PROMPT
        assert "CRITERIA COMPARISON" in DIRECTOR_EVALUATION_PROMPT
        assert "ANALYSIS PLAN" in DIRECTOR_EVALUATION_PROMPT
        assert "CONFOUNDERS" in DIRECTOR_EVALUATION_PROMPT

    def test_has_control_validation(self) -> None:
        assert "positive controls" in DIRECTOR_EVALUATION_PROMPT
        assert "negative controls" in DIRECTOR_EVALUATION_PROMPT


class TestDirectorSynthesisPrompt:
    def test_static_prompt_has_certainty_grading(self) -> None:
        assert "certainty_grading" in DIRECTOR_SYNTHESIS_PROMPT
        assert "DOWNGRADE" in DIRECTOR_SYNTHESIS_PROMPT
        assert "UPGRADE" in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_has_recommendation_strength(self) -> None:
        assert "recommendation_strength" in DIRECTOR_SYNTHESIS_PROMPT
        assert "Priority 1" in DIRECTOR_SYNTHESIS_PROMPT
        assert "Priority 4" in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_has_limitations_taxonomy(self) -> None:
        assert "limitations_taxonomy" in DIRECTOR_SYNTHESIS_PROMPT
        assert "methodology" in DIRECTOR_SYNTHESIS_PROMPT
        assert "interpretation" in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_has_knowledge_gaps(self) -> None:
        assert "knowledge_gaps" in DIRECTOR_SYNTHESIS_PROMPT
        assert "evidence map" in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_has_follow_up(self) -> None:
        assert "follow_up" in DIRECTOR_SYNTHESIS_PROMPT
        assert "computational" in DIRECTOR_SYNTHESIS_PROMPT
        assert "experimental" in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_output_has_priority(self) -> None:
        assert '"priority"' in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_output_has_certainty(self) -> None:
        assert '"certainty"' in DIRECTOR_SYNTHESIS_PROMPT
        assert '"certainty_reasoning"' in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_output_has_knowledge_gaps_field(self) -> None:
        assert '"knowledge_gaps"' in DIRECTOR_SYNTHESIS_PROMPT
        assert '"gap_type"' in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_output_has_follow_up_field(self) -> None:
        assert '"follow_up_experiments"' in DIRECTOR_SYNTHESIS_PROMPT
        assert '"impact"' in DIRECTOR_SYNTHESIS_PROMPT

    def test_static_prompt_retains_confidence(self) -> None:
        assert '"confidence": "high/medium/low"' in DIRECTOR_SYNTHESIS_PROMPT


class TestBuildSynthesisPrompt:
    def test_molecular_has_certainty_grading(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "certainty_grading" in prompt
        assert "DOWNGRADE" in prompt

    def test_molecular_has_recommendation_strength(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "recommendation_strength" in prompt
        assert "Priority 1" in prompt

    def test_molecular_has_knowledge_gaps(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "knowledge_gaps" in prompt

    def test_molecular_has_follow_up(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "follow_up" in prompt

    def test_molecular_output_has_priority(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert '"priority"' in prompt

    def test_molecular_output_has_certainty_fields(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert '"certainty"' in prompt
        assert '"certainty_reasoning"' in prompt

    def test_molecular_output_has_structured_limitations(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert '"category"' in prompt

    def test_molecular_has_priority_criteria(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "prediction_score > 0.7" in prompt
        assert "docking_score < -7" in prompt

    def test_training_has_certainty_grading(self) -> None:
        prompt = build_synthesis_prompt(TRAINING_SCIENCE)
        assert "certainty_grading" in prompt

    def test_training_has_priority_criteria(self) -> None:
        prompt = build_synthesis_prompt(TRAINING_SCIENCE)
        assert "evidence_score > 0.7" in prompt
        assert "effect_size > 0.5" in prompt

    def test_training_output_has_priority(self) -> None:
        prompt = build_synthesis_prompt(TRAINING_SCIENCE)
        assert '"priority"' in prompt

    def test_uses_domain_identifier_type(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert '"identifier_type": "smiles"' in prompt
        prompt_training = build_synthesis_prompt(TRAINING_SCIENCE)
        assert '"identifier_type": "protocol"' in prompt_training
        prompt_nutrition = build_synthesis_prompt(NUTRITION_SCIENCE)
        assert '"identifier_type": "intervention"' in prompt_nutrition

    def test_uses_domain_candidate_label(self) -> None:
        prompt = build_synthesis_prompt(MOLECULAR_SCIENCE)
        assert "candidate molecules" in prompt.lower()
        prompt_training = build_synthesis_prompt(TRAINING_SCIENCE)
        assert "training protocols" in prompt_training.lower()
        prompt_nutrition = build_synthesis_prompt(NUTRITION_SCIENCE)
        assert "nutritional interventions" in prompt_nutrition.lower()


class TestSearchToolsTracking:
    def test_includes_pubmed_training(self) -> None:
        assert "search_pubmed_training" in SEARCH_TOOLS

    def test_includes_clinical_trials(self) -> None:
        assert "search_clinical_trials" in SEARCH_TOOLS

    def test_includes_exercise_database(self) -> None:
        assert "search_exercise_database" in SEARCH_TOOLS

    def test_includes_core_literature_tools(self) -> None:
        assert "search_literature" in SEARCH_TOOLS
        assert "search_citations" in SEARCH_TOOLS
        assert "search_prior_research" in SEARCH_TOOLS


class TestLiteratureSurveyPubMedGuidance:
    def test_training_domain_includes_pubmed_guidance(self) -> None:
        prompt = build_literature_survey_prompt(TRAINING_SCIENCE, {})
        assert "search_pubmed_training" in prompt
        assert "MeSH" in prompt
        assert "search_training_literature" in prompt

    def test_molecular_domain_excludes_pubmed_guidance(self) -> None:
        prompt = build_literature_survey_prompt(MOLECULAR_SCIENCE, {})
        assert "search_pubmed_training" not in prompt

    def test_no_config_excludes_pubmed_guidance(self) -> None:
        prompt = build_literature_survey_prompt(None, {})
        assert "search_pubmed_training" not in prompt

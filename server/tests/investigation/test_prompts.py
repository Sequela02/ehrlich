from ehrlich.investigation.application.prompts import (
    DIRECTOR_EVALUATION_PROMPT,
    DIRECTOR_EXPERIMENT_PROMPT,
    RESEARCHER_EXPERIMENT_PROMPT,
    build_experiment_prompt,
    build_literature_assessment_prompt,
    build_literature_survey_prompt,
    build_pico_and_classification_prompt,
    build_researcher_prompt,
)
from ehrlich.investigation.domain.domains.molecular import MOLECULAR_SCIENCE
from ehrlich.investigation.domain.domains.sports import SPORTS_SCIENCE


class TestBuildPicoAndClassificationPrompt:
    def test_contains_categories(self) -> None:
        prompt = build_pico_and_classification_prompt()
        assert "antimicrobial" in prompt
        assert "oncology" in prompt
        assert "other" in prompt

    def test_custom_categories(self) -> None:
        cats = frozenset({"sports", "fitness"})
        prompt = build_pico_and_classification_prompt(cats)
        assert "sports" in prompt
        assert "fitness" in prompt
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

    def test_sports_domain_prompt(self) -> None:
        prompt = build_experiment_prompt(SPORTS_SCIENCE)
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

    def test_sports_domain_prompt_has_methodology(self) -> None:
        prompt = build_researcher_prompt(SPORTS_SCIENCE)
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

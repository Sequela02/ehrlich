from ehrlich.investigation.application.prompts import (
    build_literature_assessment_prompt,
    build_literature_survey_prompt,
    build_pico_and_classification_prompt,
)


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

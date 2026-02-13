"""Nutrition Science domain configuration."""

from __future__ import annotations

from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

NUTRITION_SCIENCE = DomainConfig(
    name="nutrition_science",
    display_name="Nutrition Science",
    identifier_type="intervention",
    identifier_label="Intervention",
    candidate_label="Nutritional Interventions",
    tool_tags=frozenset({"nutrition", "safety", "literature", "visualization"}),
    score_definitions=(
        ScoreDefinition(
            key="evidence_score",
            label="Evidence",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.7,
            ok_threshold=0.4,
        ),
        ScoreDefinition(
            key="effect_size",
            label="Effect Size",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.8,
            ok_threshold=0.5,
        ),
        ScoreDefinition(
            key="safety_score",
            label="Safety",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.8,
            ok_threshold=0.5,
        ),
    ),
    attribute_keys=("supplement", "dosage", "evidence_level"),
    negative_control_threshold=0.5,
    hypothesis_types=("mechanistic", "efficacy", "safety", "dose_response"),
    valid_domain_categories=(
        "nutrition_science",
        "sports_nutrition",
        "dietary_supplements",
        "clinical_nutrition",
        "food_science",
    ),
    template_prompts=(
        {
            "title": "Creatine for Strength",
            "domain": "Sports Nutrition",
            "prompt": (
                "What is the evidence for creatine monohydrate supplementation "
                "on strength and power performance? Analyze dosing protocols, "
                "loading phases, and safety profile from meta-analyses."
            ),
        },
    ),
    director_examples="""\
<examples>
<example>
<research_question>What is the evidence for creatine \
on strength performance?</research_question>
<hypotheses>
[
  {{
    "statement": "Creatine monohydrate supplementation (3-5g/day) \
improves maximal strength by >5% in resistance-trained individuals",
    "rationale": "Creatine increases phosphocreatine stores, \
enabling greater ATP resynthesis during high-intensity exercise",
    "prediction": "Meta-analyses will show effect sizes >0.3 \
for 1RM improvements with creatine vs placebo",
    "null_prediction": "No significant strength difference \
between creatine and placebo (effect size <0.1)",
    "success_criteria": ">=3 meta-analyses showing significant \
strength improvement with pooled effect size >0.3",
    "failure_criteria": "<2 studies showing benefit or \
inconsistent findings with high heterogeneity",
    "scope": "Resistance-trained adults, 4-12 week supplementation periods",
    "hypothesis_type": "efficacy",
    "prior_confidence": 0.80
  }}
],
"negative_controls": [
  {{"identifier": "Maltodextrin placebo", "name": "Carbohydrate placebo", \
"source": "Isocaloric placebo with no ergogenic properties; \
expected no strength effect"}}
],
"positive_controls": [
  {{"identifier": "Creatine monohydrate 20g/day loading + 5g/day maintenance", \
"name": "Standard loading protocol", \
"known_activity": "Strength improvement d=0.4-0.6 in multiple meta-analyses", \
"source": "ISSN position stand, well-established protocol"}}
]
</hypotheses>
</example>
</examples>""",
    experiment_examples="""\
<examples>
<example>
<hypothesis>Creatine monohydrate improves maximal \
strength</hypothesis>
<output>
{{
  "description": "Search for meta-analyses on creatine and strength, \
analyze effect sizes and safety data",
  "tool_plan": ["search_supplement_evidence", \
"search_supplement_labels", "search_supplement_safety", \
"search_nutrient_data", "assess_nutrient_adequacy", \
"check_interactions", "analyze_nutrient_ratios"],
  "independent_variable": "Creatine supplementation (3-5g/day vs placebo)",
  "dependent_variable": "Maximal strength (1RM, effect size d)",
  "controls": ["positive: standard loading protocol (20g/day x 5 days)", \
"negative: maltodextrin placebo"],
  "confounders": ["Training status variability", \
"Dietary protein intake", "Supplementation duration"],
  "analysis_plan": "Primary: pooled effect size with 95% CI; \
secondary: adverse event incidence rate; expect N>=5 RCTs",
  "success_criteria": "Pooled effect size >0.3 with p<0.05 \
and no serious adverse events",
  "failure_criteria": "Effect size <0.1 or significant \
safety concerns from CAERS data"
}}
</output>
</example>
</examples>""",
    synthesis_scoring_instructions="""\
For each nutritional intervention candidate, provide:
- evidence_score (0-1): overall evidence quality based on study count, design, and consistency
- effect_size (Cohen's d): pooled effect size from meta-analyses
- safety_score (0-1): safety profile (1.0 = excellent safety, 0.0 = serious concerns)
- supplement: supplement or nutrient name
- dosage: recommended dosage range
- evidence_level: evidence quality grade (A/B/C/D)

Priority assignment:
- Priority 1: evidence_score > 0.7 AND effect_size > 0.3 AND safety_score > 0.8
- Priority 2: meets 2 of 3 criteria above
- Priority 3: meets 1 criterion or limited evidence
- Priority 4: safety concerns or contradictory evidence""",
)

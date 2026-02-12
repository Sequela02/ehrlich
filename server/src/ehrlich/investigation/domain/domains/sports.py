"""Sports Science domain configuration."""

from __future__ import annotations

from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

SPORTS_SCIENCE = DomainConfig(
    name="sports_science",
    display_name="Sports Science",
    identifier_type="protocol",
    identifier_label="Protocol",
    candidate_label="Training Protocols",
    tool_tags=frozenset(
        {
            "sports",
            "literature",
        }
    ),
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
            key="confidence",
            label="Confidence",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.7,
            ok_threshold=0.4,
        ),
    ),
    attribute_keys=("sport", "training_type", "evidence_level"),
    negative_control_threshold=0.5,
    visualization_type="table",
    hypothesis_types=(
        "physiological",
        "performance",
        "epidemiological",
        "mechanistic",
    ),
    valid_domain_categories=(
        "sports_science",
        "exercise_physiology",
        "sports_medicine",
        "biomechanics",
        "sports_nutrition",
    ),
    template_prompts=(
        {
            "title": "VO2max Training Optimization",
            "domain": "Exercise Physiology",
            "prompt": (
                "What are the most effective training protocols for improving "
                "VO2max in recreational runners? Compare high-intensity interval "
                "training (HIIT) vs polarized training vs threshold training, "
                "considering evidence quality, effect sizes, and injury risk."
            ),
        },
        {
            "title": "ACL Injury Prevention",
            "domain": "Sports Medicine",
            "prompt": (
                "Evaluate evidence-based neuromuscular training programs for ACL "
                "injury prevention in female soccer players. Analyze which exercise "
                "components (plyometrics, balance, strength) have the strongest "
                "protective effect and optimal training frequency."
            ),
        },
    ),
    director_examples="""\
<examples>
<example>
<research_question>What are the most effective training \
protocols for improving VO2max?</research_question>
<hypotheses>
[
  {{
    "statement": "HIIT produces greater VO2max improvements \
than MICT in recreational athletes",
    "rationale": "HIIT provides greater stimulus to central \
and peripheral oxygen transport systems",
    "prediction": "HIIT protocols will show effect sizes \
>0.5 for VO2max improvement vs MICT controls",
    "null_prediction": "No significant difference in VO2max \
between HIIT and MICT (effect size <0.2)",
    "success_criteria": ">=3 meta-analyses showing HIIT \
superiority with pooled effect size >0.5",
    "failure_criteria": "<2 studies showing significant \
advantage or conflicting high-heterogeneity results",
    "scope": "Recreational athletes, 8-12 week interventions",
    "hypothesis_type": "physiological",
    "prior_confidence": 0.70
  }}
],
"negative_controls": [
  {{"identifier": "Passive stretching only", "name": "Static stretching control", \
"source": "No cardiovascular stimulus; expected no VO2max change"}}
],
"positive_controls": [
  {{"identifier": "Tabata 4x4 HIIT protocol", "name": "Tabata protocol", \
"known_activity": "VO2max improvement d=0.8-1.2 in multiple meta-analyses", \
"source": "Gold standard HIIT protocol with large, consistent effect sizes"}}
]
</hypotheses>
</example>
<example>
<research_question>Evaluate neuromuscular training for \
ACL injury prevention</research_question>
<hypotheses>
[
  {{
    "statement": "Neuromuscular training with plyometrics \
reduces ACL injury incidence by >50% in female athletes",
    "rationale": "Plyometric training improves landing \
mechanics, knee valgus, and hamstring:quad ratio",
    "prediction": "Programs with plyometrics will show \
relative risk reduction >0.50 for ACL injuries",
    "null_prediction": "No significant reduction in ACL \
injury rates with plyometric programs (RR >0.80)",
    "success_criteria": ">=2 RCTs or meta-analyses \
demonstrating >50% risk reduction",
    "failure_criteria": "Risk reduction <30% or \
inconsistent findings across studies",
    "scope": "Female team sport athletes, ages 14-25",
    "hypothesis_type": "epidemiological",
    "prior_confidence": 0.65
  }}
],
"negative_controls": [
  {{"identifier": "Flexibility-only program", "name": "Stretching control", \
"source": "No neuromuscular component; expected no ACL risk reduction"}}
],
"positive_controls": [
  {{"identifier": "FIFA 11+ neuromuscular warm-up", "name": "FIFA 11+", \
"known_activity": "ACL injury risk reduction RR=0.35-0.50 in RCTs", \
"source": "WHO-endorsed program with strong meta-analytic evidence"}}
]
</hypotheses>
</example>
</examples>""",
    experiment_examples="""\
<examples>
<example>
<hypothesis>HIIT produces greater VO2max improvements \
than MICT</hypothesis>
<output>
{{
  "description": "Search for meta-analyses comparing \
HIIT vs MICT for VO2max, then analyze effect sizes",
  "tool_plan": ["search_sports_literature", \
"analyze_training_evidence", "compare_protocols"],
  "independent_variable": "Training protocol type (HIIT vs MICT)",
  "dependent_variable": "VO2max improvement (mL/kg/min, effect size d)",
  "controls": ["positive: known effective HIIT protocol (Tabata 4x4)", \
"negative: sedentary control group data"],
  "confounders": ["Baseline fitness differences", \
"Study duration variability (6-16 weeks)", \
"HIIT protocol heterogeneity"],
  "analysis_plan": "Primary: pooled effect size (Cohen's d) with 95% CI; \
secondary: heterogeneity (I^2); expect N>=5 studies per comparison",
  "success_criteria": "Pooled effect size >0.5 with I^2 <75%",
  "failure_criteria": "Effect size <0.2 or I^2 >75% indicating \
inconsistent findings"
}}
</output>
</example>
</examples>""",
    synthesis_scoring_instructions="""\
For each training protocol candidate, provide:
- evidence_score (0-1): overall evidence quality based on study count and quality
- effect_size (Cohen's d): pooled effect size from meta-analyses
- confidence (0-1): confidence in the recommendation considering heterogeneity
- sport: target sport or population
- training_type: type of training (HIIT, strength, plyometric, etc.)
- evidence_level: evidence quality grade (A/B/C/D)""",
)

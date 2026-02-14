"""Impact Evaluation domain configuration."""

from __future__ import annotations

from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

IMPACT_EVALUATION = DomainConfig(
    name="impact_evaluation",
    display_name="Impact Evaluation",
    identifier_type="program",
    identifier_label="Program",
    candidate_label="Program Interventions",
    tool_tags=frozenset({"impact", "statistics", "literature", "visualization", "ml"}),
    score_definitions=(
        ScoreDefinition(
            key="effect_size",
            label="Effect Size",
            format_spec=".3f",
            higher_is_better=True,
            good_threshold=0.5,
            ok_threshold=0.2,
        ),
        ScoreDefinition(
            key="statistical_significance",
            label="Significance",
            format_spec=".4f",
            higher_is_better=False,
            good_threshold=0.01,
            ok_threshold=0.05,
        ),
        ScoreDefinition(
            key="evidence_tier",
            label="Evidence Tier",
            format_spec=".0f",
            higher_is_better=True,
            good_threshold=3.0,
            ok_threshold=2.0,
        ),
        ScoreDefinition(
            key="cost_effectiveness",
            label="Cost-Effectiveness",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.7,
            ok_threshold=0.4,
        ),
    ),
    attribute_keys=("sector", "country", "method", "evidence_tier"),
    negative_control_threshold=0.5,
    hypothesis_types=("causal", "comparative", "cost_effectiveness", "equity"),
    valid_domain_categories=(
        "impact_evaluation",
        "program_evaluation",
        "social_program",
        "public_policy",
        "policy_analysis",
    ),
    template_prompts=(
        {
            "title": "Education Program Impact",
            "domain": "Impact Evaluation",
            "prompt": (
                "What is the causal effect of conditional cash transfer programs "
                "on school enrollment and attendance in Latin America? Compare "
                "Prospera (Mexico), Bolsa Familia (Brazil), and Familias en Accion "
                "(Colombia) using available outcome data."
            ),
        },
        {
            "title": "Health Intervention Effectiveness",
            "domain": "Impact Evaluation",
            "prompt": (
                "Evaluate the impact of community health worker programs on "
                "maternal mortality and childhood vaccination rates in "
                "sub-Saharan Africa. Use WHO and World Bank indicators."
            ),
        },
        {
            "title": "Sports Program Social Impact",
            "domain": "Impact Evaluation",
            "prompt": (
                "Does youth sports program participation reduce juvenile "
                "delinquency and improve educational outcomes? Analyze the "
                "evidence from after-school sports interventions."
            ),
        },
    ),
    director_examples="""\
<examples>
<example>
<research_question>What is the causal effect of conditional cash \
transfers on school enrollment?</research_question>
<hypotheses>
[
  {{
    "statement": "Conditional cash transfer programs increase \
primary school enrollment by 5-15 percentage points in \
low-income countries",
    "rationale": "Economic theory predicts that reducing the \
opportunity cost of schooling through cash transfers conditional \
on enrollment will increase human capital investment",
    "prediction": "World Bank and WHO data will show enrollment \
rate increases of 5-15pp in treatment regions compared to \
pre-program baselines and non-program regions",
    "null_prediction": "No significant difference in enrollment \
rates between treatment and control regions (effect < 2pp)",
    "success_criteria": ">=3 country datasets showing statistically \
significant enrollment increases with effect sizes > 5pp",
    "failure_criteria": "Fewer than 2 datasets showing significant \
effects, or effects below 2pp",
    "scope": "Low and middle-income countries with established CCT \
programs, 2000-2024",
    "hypothesis_type": "causal",
    "prior_confidence": 0.75
  }}
],
"negative_controls": [
  {{"identifier": "Non-intervention comparison region", \
"name": "Control region without CCT", \
"source": "Matched region without program implementation; \
expected no enrollment change beyond secular trend"}}
],
"positive_controls": [
  {{"identifier": "Prospera (Mexico) 1997-2010", \
"name": "Well-documented CCT with RCT evaluation", \
"known_activity": "Enrollment increase of 3-9pp documented \
in IFPRI evaluation (Schultz 2004)", \
"source": "Multiple RCT evaluations, World Bank reports"}}
]
</hypotheses>
</example>
</examples>""",
    experiment_examples="""\
<examples>
<example>
<hypothesis>Conditional cash transfers increase school \
enrollment</hypothesis>
<output>
{{
  "description": "Gather enrollment indicators from World Bank \
and WHO, compare treatment vs control periods/regions, \
test statistical significance",
  "tool_plan": ["search_economic_indicators", \
"fetch_benchmark", "compare_programs", \
"run_statistical_test", "search_literature"],
  "independent_variable": "CCT program implementation \
(present vs absent)",
  "dependent_variable": "Primary school net enrollment rate (%)"\
,
  "controls": ["positive: Prospera program with known 3-9pp \
effect", "negative: matched non-program region"],
  "confounders": ["GDP growth trends", "Demographic shifts", \
"Other education policies", "Urbanization"],
  "analysis_plan": "Primary: difference-in-differences of \
enrollment rates; secondary: dose-response by transfer amount; \
expect N>=5 country-year observations per group",
  "success_criteria": "Enrollment increase >5pp with p<0.05 \
and consistent across >=2 countries",
  "failure_criteria": "Effect <2pp or p>0.10 or inconsistent \
direction across countries"
}}
</output>
</example>
</examples>

<tool_examples>
Example: Searching for development indicators
1. search_economic_indicators(query="SE.PRM.ENRR", \
source="world_bank", country="MX", start_year=2000, end_year=2020)
2. search_economic_indicators(query="SH.STA.MMRT", \
source="who", country="MEX")
3. record_finding(title="Enrollment trends in Mexico 2000-2020", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Fetching benchmark data for comparison
1. fetch_benchmark(indicator="SE.PRM.ENRR", source="world_bank", \
country="MX", period="2010-2020")
2. fetch_benchmark(indicator="SE.PRM.ENRR", source="world_bank", \
country="BR", period="2010-2020")
3. record_finding(title="Cross-country enrollment comparison", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Comparing program outcomes statistically
1. compare_programs(programs='[{{"name": "Treatment", \
"values": [85.2, 87.1, 89.3]}}, {{"name": "Control", \
"values": [78.1, 78.5, 79.0]}}]', metric="enrollment_rate")
2. run_statistical_test(group_a="85.2,87.1,89.3,90.1,88.5", \
group_b="78.1,78.5,79.0,78.8,79.2", test="auto")
3. record_finding(title="Significant enrollment difference", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Training a classifier on program outcome data
1. train_classifier(feature_names=["budget_per_capita", \
"duration_years", "coverage_pct", "gdp_per_capita"], \
feature_values=[...], labels=[1.0, 0.0, ...], \
target_name="program success")
2. predict_scores(feature_names=[...], feature_values=[...], \
model_id="xgboost_program_abc123")
3. record_finding(title="ML model predicts program success", \
detail="...", hypothesis_id="h1", evidence_type="supporting")
</tool_examples>""",
    synthesis_scoring_instructions="""\
For each program intervention candidate, provide:
- effect_size (Cohen's d or pp difference): magnitude of causal effect
- statistical_significance (p-value): significance level of the estimate
- evidence_tier (1-4): 4=strong (RCT), 3=moderate (quasi-experimental), \
2=promising (correlational), 1=rationale (descriptive)
- cost_effectiveness (0-1): cost-effectiveness ratio relative to alternatives
- sector: program sector (education, health, employment, housing, sports)
- country: country ISO code
- method: causal identification method used (DiD, PSM, RDD, RCT)
- evidence_tier: WWC tier label (strong/moderate/promising/rationale)

Priority assignment:
- Priority 1: effect_size > 0.5 AND p < 0.01 AND evidence_tier >= 3
- Priority 2: effect_size > 0.2 AND p < 0.05 AND evidence_tier >= 2
- Priority 3: effect_size > 0.1 OR evidence_tier >= 2
- Priority 4: weak evidence or methodological concerns""",
)

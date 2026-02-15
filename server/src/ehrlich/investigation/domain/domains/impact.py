"""Impact Evaluation domain configuration."""

from __future__ import annotations

from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

IMPACT_EVALUATION = DomainConfig(
    name="impact_evaluation",
    display_name="Impact Evaluation",
    identifier_type="program",
    identifier_label="Program",
    candidate_label="Program Interventions",
    tool_tags=frozenset({"impact", "causal", "statistics", "literature", "visualization", "ml"}),
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
        "us_federal_program",
        "education_policy",
        "housing_policy",
        "labor_market",
        "public_health",
        "mexico_social_program",
        "coneval_evaluation",
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
        {
            "title": "SNAP Benefits & Nutrition",
            "domain": "Impact Evaluation",
            "prompt": (
                "What is the causal effect of SNAP (food stamps) benefits "
                "on food security and nutrition outcomes in US households? "
                "Use USAspending data for program scale and Census/BLS for "
                "demographic context."
            ),
        },
        {
            "title": "Pell Grant & College Completion",
            "domain": "Impact Evaluation",
            "prompt": (
                "Do Pell Grant recipients have different completion rates "
                "and post-graduation earnings compared to non-recipients? "
                "Analyze College Scorecard data across institution types."
            ),
        },
        {
            "title": "Housing Vouchers & Mobility",
            "domain": "Impact Evaluation",
            "prompt": (
                "What is the effect of Section 8 housing vouchers on "
                "economic mobility and neighborhood quality? Compare HUD "
                "Fair Market Rents with Census income data across states."
            ),
        },
        {
            "title": "CONEVAL Program Evaluation (Mexico)",
            "domain": "Impact Evaluation",
            "prompt": (
                "Evaluate the impact of Becas Benito Juarez (Mexico) on "
                "school retention using CONEVAL methodology. Use INEGI "
                "education indicators and datos.gob.mx datasets to assess "
                "outcomes against CREMAA quality criteria."
            ),
        },
        {
            "title": "Mexico Macroeconomic Impact",
            "domain": "Impact Evaluation",
            "prompt": (
                "How have Banxico monetary policy interventions affected "
                "inflation and the exchange rate in Mexico from 2020-2024? "
                "Use INEGI inflation indicators and Banxico SIE series data "
                "for difference-in-differences analysis."
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
  "dependent_variable": "Primary school net enrollment rate (%)",
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

Example: Searching US labor data from BLS
1. search_economic_indicators(query="LNS14000000", \
source="bls", limit=5)
2. record_finding(title="US unemployment rate trends", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching US Census demographics
1. search_economic_indicators(query="median_income", \
source="census", start_year=2020, end_year=2022)
2. record_finding(title="Median income by state", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching CDC health data
1. search_health_indicators(indicator="mortality", source="cdc", \
year_start=2015, year_end=2022)
2. record_finding(title="US mortality trends", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Fetching benchmark data for comparison
1. fetch_benchmark(indicator="SE.PRM.ENRR", source="world_bank", \
country="MX", period="2010-2020")
2. fetch_benchmark(indicator="SE.PRM.ENRR", source="world_bank", \
country="BR", period="2010-2020")
3. record_finding(title="Cross-country enrollment comparison", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching federal spending data
1. search_spending_data(query="Head Start", \
agency="Department of Health and Human Services", year=2023)
2. record_finding(title="Head Start federal spending 2023", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching education outcomes
1. search_education_data(query="community college", state="CA", limit=10)
2. record_finding(title="CA community college outcomes", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching housing data
1. search_housing_data(state="CA", year=2024)
2. record_finding(title="California Fair Market Rents 2024", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Discovering open datasets
1. search_open_data(query="poverty education", organization="ed-gov")
2. record_finding(title="Available federal datasets", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Comparing program outcomes statistically
1. compare_programs(programs='[{{"name": "Treatment", \
"values": [85.2, 87.1, 89.3]}}, {{"name": "Control", \
"values": [78.1, 78.5, 79.0]}}]', metric="enrollment_rate")
2. run_statistical_test(group_a="85.2,87.1,89.3,90.1,88.5", \
group_b="78.1,78.5,79.0,78.8,79.2", test="auto")
3. record_finding(title="Significant enrollment difference", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Running difference-in-differences estimation
1. estimate_did(treatment_pre="[78.5, 79.2, 80.1]", \
treatment_post="[88.3, 89.1, 90.5]", \
control_pre="[77.8, 78.5, 79.0]", \
control_post="[79.1, 79.8, 80.2]")
2. assess_threats(method="did", \
sample_sizes='{{"treatment": 6, "control": 6}}', \
parallel_trends_p=0.45, effect_size=0.8)
3. record_finding(title="DiD shows significant enrollment effect", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Propensity score matching
1. estimate_psm(treated_outcomes="[92.3, 94.1, 93.5, 91.0]", \
control_outcomes="[85.1, 85.8, 85.3, 86.0]", \
treated_covariates="[[1.2, 3.4], [2.1, 4.5], [1.8, 3.9], [2.0, 4.2]]", \
control_covariates="[[1.0, 3.2], [2.3, 4.1], [1.5, 3.6], [1.9, 4.0]]")
2. record_finding(title="PSM estimate of program effect", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Regression discontinuity design
1. estimate_rdd(running_variable="[45, 48, 49, 50, 51, 52, 55]", \
outcome="[70, 72, 73, 80, 82, 83, 85]", cutoff=50.0, design="sharp")
2. record_finding(title="RDD shows enrollment discontinuity at cutoff", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Synthetic control method
1. estimate_synthetic_control(\
treated_series="[10, 11, 12, 20, 22, 25]", \
donor_matrix="[[10, 11, 12, 13, 14, 15], [9, 10, 11, 12, 13, 14]]", \
treatment_period=3)
2. record_finding(title="Synthetic control shows treatment effect", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Cost-effectiveness analysis
1. compute_cost_effectiveness(program_name="CCT Program", \
total_cost=5000000.0, total_effect=1500.0, \
currency="USD", effect_unit="additional enrollees")
2. record_finding(title="Cost per additional enrollee", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching INEGI economic data for Mexico
1. search_economic_indicators(query="inflacion", source="inegi")
2. search_economic_indicators(query="493911", source="inegi")
3. record_finding(title="Mexico GDP trend from INEGI", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Searching Banxico financial series
1. search_economic_indicators(query="tipo de cambio", source="banxico")
2. search_economic_indicators(query="SF60653", source="banxico")
3. record_finding(title="MXN/USD exchange rate from Banxico SIE", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Discovering Mexican open government datasets
1. search_open_data(query="programa social educacion", source="datosgob")
2. search_open_data(query="salud publica", source="datosgob", \
organization="ssa")
3. record_finding(title="Mexican open datasets on education programs", \
detail="...", hypothesis_id="h1", evidence_type="supporting")

Example: Validating MIR indicators with CREMAA criteria
1. analyze_program_indicators(\
indicator_name="Porcentaje de beneficiarios con mejora educativa", \
level="proposito")
2. record_finding(title="CREMAA validation of MIR indicator", \
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

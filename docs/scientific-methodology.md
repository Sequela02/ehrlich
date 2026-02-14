# Scientific Methodology

> Part of the [development roadmap](roadmap.md). This is a cross-cutting upgrade that applies to all investigation phases.

Ehrlich grounds every phase of its investigation workflow in established scientific methodology. Each phase is backed by research from the world's best scientists and epistemological frameworks.

## Philosophy

A hypothesis without a prediction is an opinion, not science. An experiment without pre-defined criteria is exploration, not testing. Evidence without provenance is hearsay, not data.

Ehrlich treats these principles as engineering requirements, not aspirations.

## Phase-by-Phase Methodology

### Phase 1: Hypothesis Formulation -- UPGRADED

**Status:** Complete. Grounded in 9 frameworks spanning 130+ years.

**Sources:**
- Popper (1934) -- Falsifiability: hypothesis must be refutable by possible observations
- Chamberlin (1890) -- Multiple Working Hypotheses: competing alternatives prevent confirmation bias
- Platt (1964) -- Strong Inference: crucial experiments that exclude hypotheses with defined outcomes
- Feynman (1964) -- Guess, compute consequences, compare with experiment
- Lakatos (1978) -- Progressive research programmes predict novel facts
- PICO (1995) -- Population, Intervention, Comparison, Outcome: structured decomposition
- Bayesian Updating -- Prior probability updates to posterior with evidence
- Lipinski Rule of Five -- Gold standard: quantitative, testable, falsifiable, clear boundaries
- Google AI Co-Scientist (2025) -- Hypothesis + mechanism + testability + novelty + evaluation criteria

**8 Universal Components (all experts converge on):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | Claim | Testable statement of what you believe |
| 2 | Mechanism | Causal explanation (HOW, not just WHY) |
| 3 | Prediction | "If true, we will observe X" |
| 4 | Falsification | "Wrong if we observe Y" + quantitative thresholds |
| 5 | Scope | Boundary conditions (organism, compound class, domain) |
| 6 | Alternatives | Competing explanations for the same phenomenon |
| 7 | Evidence strength | Not all evidence equal; weight matters |
| 8 | Prior confidence | Bayesian prior (before testing) that updates to posterior |

**Implementation:**
```
Hypothesis entity fields:
  statement           -- the testable claim
  rationale           -- causal mechanism (HOW)
  prediction          -- "If true, we expect to observe X"
  null_prediction     -- "If false, we would observe Y"
  success_criteria    -- quantitative threshold for support
  failure_criteria    -- quantitative threshold for refutation
  scope               -- boundary conditions
  hypothesis_type     -- mechanistic / structural / pharmacological / toxicological / physiological / performance / epidemiological
  prior_confidence    -- Bayesian prior (0.0-1.0, set at formulation)
  confidence          -- Bayesian posterior (updated after evaluation)
```

**Key design decisions:**
- Success/failure criteria live on the Hypothesis, not the Experiment. The hypothesis defines WHAT to measure; the experiment defines HOW to measure it. Evaluation compares observations against pre-defined criteria (objective) instead of subjective judgment.
- `hypothesis_type` spans domains: molecular science uses mechanistic/structural/pharmacological/toxicological; training science uses physiological/performance/epidemiological; nutrition science uses mechanistic/efficacy/safety/dose_response. `DomainConfig.hypothesis_types` defines valid types per domain.
- `DomainConfig` serves as the extension point for domain-specific validation and synthesis methodology (Phases 5-6).

---

### Phase 2: Literature Survey -- UPGRADED

**Status:** Complete. Grounded in 27 verified sources. Rapid scoping review methodology (Arksey & O'Malley 2005, Cochrane 2020).

**Sources:**
- Arksey & O'Malley (2005) -- Scoping review framework (5 stages)
- Greenhalgh & Peacock (2005) -- Citation chasing (snowballing): 51% of sources come from non-database strategies
- PRISMA 2020 (Page et al., 2021) -- Transparent search reporting
- GRADE (Guyatt et al., 2008) -- Body-of-evidence certainty grading (high/moderate/low/very_low)
- AMSTAR 2 (Shea et al., 2017) -- Critical appraisal of systematic reviews
- Oxford CEBM (2011) -- 6-level evidence hierarchy (systematic review → expert opinion)

**10 Universal Components (all experts converge on):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | PICO Decomposition | Population, Intervention, Comparison, Outcome from research question |
| 2 | Multi-Strategy Search | Database queries + citation chasing + dataset exploration |
| 3 | Citation Chasing | Forward/backward snowballing via references and citing papers |
| 4 | Evidence Hierarchy | 6-level grading per finding (1=systematic review → 6=expert opinion) |
| 5 | Saturation Rule | Stop when additional queries yield <2 new unique results |
| 6 | Source Provenance | Every finding tracked to API source (ChEMBL, PDB, DOI, etc.) |
| 7 | Body-of-Evidence Grading | GRADE-adapted aggregate grade (high/moderate/low/very_low) |
| 8 | Quality Self-Assessment | AMSTAR-2-adapted check against 4 rapid-review quality domains |
| 9 | Structured Context | XML-formatted PICO + graded findings passed to hypothesis formulation |
| 10 | Transparent Documentation | `LiteratureSurveyCompleted` event with search stats for audit trail |

**Implementation:**
```
Pipeline order: Classification+PICO → Literature Survey → Formulation (was: Literature → Classification → Formulation)

Phase 1 (Haiku): Merged PICO decomposition + domain classification in single call
  Output: {domain, population, intervention, comparison, outcome, search_terms}

Phase 2 (Sonnet researcher + Haiku):
  A. Structured search with domain-filtered tools + citation chasing (search_citations tool)
  B. Findings recorded with evidence_level (1-6) and source provenance
  C. Body-of-evidence grading via Haiku (GRADE-adapted)
  D. Self-assessment against 4 AMSTAR-2-adapted quality domains
  E. LiteratureSurveyCompleted event emitted with PICO, stats, grade, assessment

Formulation context: Structured XML replaces raw text summary
  <literature_survey>
    <pico population="..." intervention="..." comparison="..." outcome="..."/>
    <evidence_grade>moderate</evidence_grade>
    <search_stats queries="5" total="47" included="12"/>
    <findings>...</findings>
  </literature_survey>
```

**Key design decisions:**
- PICO + domain classification merged into single Haiku call (eliminates one API call, makes literature survey domain-aware from start)
- Pipeline reordered: classify first, then literature, so researcher gets domain-filtered tools
- `search_citations` tool for snowballing (Greenhalgh & Peacock: 51% of sources from non-database strategies)
- `evidence_level` on Finding entity (int, 0=unrated, 1-6 per hierarchy) -- not a boolean, supports granular grading
- Body-of-evidence grading via separate Haiku call after search (not during) -- separates data collection from assessment
- Structured XML context replaces raw `literature_summary[:3000]` -- Director receives typed, parseable literature data

---

### Phase 3: Experiment Design -- UPGRADED

**Status:** Complete. Grounded in 20 universal components from Fisher (1935), Platt (1964), Cohen (1988), Saltelli (2008), OECD (2007), Tropsha (2010), and others.

**Sources:**
- Fisher (1935) -- Randomization, replication, blocking
- Platt (1964) -- Strong inference: crucial experiments that exclude hypotheses
- Cohen (1988) -- Statistical power and effect sizes
- Saltelli (2008) -- Sensitivity analysis: global methods for model robustness
- OECD (2007) -- Applicability domain for QSAR model predictions
- Tropsha (2010) -- Best practices for QSAR development and validation
- Fanelli (2012) -- Negative results reporting and publication bias
- Oberkampf & Roy (2010) -- Verification vs. validation in computational science

**10 Universal Components (implemented):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | Independent Variable | Factor being manipulated (e.g., compound structure, training protocol, supplement dose) |
| 2 | Dependent Variable | Outcome being measured (e.g., Ki/IC50, docking score, effect size, evidence grade) |
| 3 | Controls | Positive (known active) and negative (known inactive) baselines |
| 4 | Confounders | Identified threats to validity (dataset bias, measurement error, confounding variables) |
| 5 | Analysis Plan | Pre-specified metrics and thresholds (prevents post-hoc rationalization) |
| 6 | Success Criteria | Quantitative threshold for supporting the hypothesis |
| 7 | Failure Criteria | Quantitative threshold for refuting the hypothesis |
| 8 | Sensitivity | Robustness check: does conclusion change with parameter variation? |
| 9 | Applicability Domain | ML predictions checked against training data similarity |
| 10 | Negative Results | Failed approaches recorded with diagnosis, not omitted |

**Implementation:**
```
Experiment entity fields (7 new protocol fields):
  independent_variable  -- factor being manipulated
  dependent_variable    -- outcome being measured
  controls              -- positive/negative baselines
  confounders           -- identified threats to validity
  analysis_plan         -- pre-specified metrics/thresholds
  success_criteria      -- from Director design (experiment-level)
  failure_criteria      -- from Director design (experiment-level)

Director experiment prompt: +<methodology> section with 5 principles
  (VARIABLES, CONTROLS, CONFOUNDERS, ANALYSIS PLAN, SENSITIVITY)
  ANALYSIS PLAN principle instructs Director to plan statistical tests
  (test type, alpha, effect size threshold) when designing experiments

Experiment design schema: optional statistical_test_plan field
  {test_type, alpha, effect_size_threshold, data_source}

Researcher experiment prompt: +<methodology> section with 6 principles
  (SENSITIVITY, APPLICABILITY DOMAIN, UNCERTAINTY, VERIFICATION, NEGATIVE RESULTS, STATISTICAL TESTING)
  Principle #6 instructs Researcher to call run_statistical_test or run_categorical_test
  after gathering comparison data, and record results as findings with evidence_type
  based on significance

Director evaluation prompt: +<methodology_checks> section
  (control validation, criteria comparison, analysis plan adherence, confounder check)

Orchestrator wiring:
  - Experiment creation reads all 7 fields from Director design output
  - ExperimentStarted event carries protocol fields to frontend
  - Researcher context includes experiment controls, analysis plan, criteria
  - Evaluator context includes experiment-level protocol for criteria comparison
```

**Key design decisions:**
- Experiment-level criteria complement hypothesis-level criteria: hypothesis defines WHAT to measure, experiment defines HOW to measure it with specific protocol
- Controls are strings (free-form "positive: Avibactam (Ki ~1 nM)") rather than structured entities -- keeps the schema simple while allowing domain-specific descriptions
- Analysis plan is pre-specified (before seeing results) to prevent post-hoc rationalization (Fisher's principle)
- Confounders are explicitly identified at design time so the evaluator can check if they materialized
- `expected_findings` removed from Director output format (was never read by orchestrator)
- Domain config examples updated with protocol fields for molecular, training, and nutrition science

**Parallel researcher differentiation (3 layers):**

Hypotheses are tested in parallel batches of 2. Without differentiation, parallel researchers can converge on identical API queries, duplicate ML models, or execute near-identical tool sequences. Three layers prevent this:

1. **Orthogonal hypothesis formulation** -- Director prompt includes explicit diversity principle: each hypothesis must attack a different mechanism, pathway, or data source. Different validation strategies required (e.g., ML prediction vs structural docking vs substructure enrichment).

2. **Sibling-aware experiment design** -- Experiments are designed sequentially within a batch. Experiment 2+ receives a `<sibling_experiments>` XML block containing prior designs (hypothesis, description, tool plan), with instructions to use different tools, data sources, or validation strategies.

3. **Researcher sibling context** -- Each parallel researcher receives a `<parallel_experiment>` XML block describing the other's hypothesis, experiment, and tool plan. This lets researchers actively differentiate at query time (different search terms, data sources, analytical approaches) even when their designs are already orthogonal.

---

### Phase 4: Evidence Evaluation -- UPGRADED

**Status:** Complete. Grounded in 47 verified sources spanning evidence hierarchies (Burns & Chung), effect sizes (Cohen), Bayesian updating (Kass & Raftery, Jeffreys), contradiction resolution (Lakatos, Hunter & Schmidt), and convergence of evidence (Munafo et al.). See [evidence-evaluation.md](../research/methodology/evidence-evaluation.md).

**Sources:**
- Burns & Chung (2011) -- Evidence hierarchy (8-tier ranking by directness, reproducibility, controls)
- Cohen (1988) -- Effect size benchmarks (d=0.2 small, 0.5 medium, 0.8 large)
- Kramer et al. (2012) -- Experimental uncertainty: IC50 reproducibility +/-0.3 log (intra-lab), +/-0.5 log (cross-lab)
- Chen (2015) -- Docking score uncertainty: <0.5 kcal/mol is noise
- Kass & Raftery (1995) -- Bayes factors for sequential hypothesis confidence update
- Jeffreys (1961) -- BF interpretation scale (1-3 barely, 3-20 positive, 20-150 strong)
- Munafo et al. (2021) -- Triangulation: independent methods agreeing strengthens causal inference
- Lakatos (1978) -- Contradiction resolution: compound identity → assay comparability → temporal → severity
- Hunter & Schmidt (1990) -- Meta-analytic correction for contradictory evidence

**8 Universal Components (implemented via Director evaluation prompt):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | Evidence Hierarchy | 8-tier ranking from replicated experimental data (highest) to qualitative literature (lowest) |
| 2 | Effect Size Thresholds | Domain-specific noise floors (molecular: IC50 <2-fold, docking <0.5 kcal/mol; training: Cohen's d threshold; nutrition: effect size threshold) |
| 3 | Bayesian Updating | Prior confidence × evidence multiplier → posterior (supporting tiers 1-3: ×1.3-1.5, contradicting: ×0.3-0.5) |
| 4 | Contradiction Resolution | 4-step hierarchy: identity check → assay comparability → temporal relevance → severity classification |
| 5 | Convergence Check | Independent method agreement (converging/mixed/contradictory) modulates confidence |
| 6 | Methodology Checks | Control validation, criteria comparison, analysis plan adherence, confounder check |
| 7 | Certainty of Evidence | GRADE-adapted grading (high/moderate/low/very_low) per hypothesis |
| 8 | Evidence Convergence | Explicit convergence/divergence status across method types |

**Implementation:**
```
Hypothesis entity field:
  certainty_of_evidence  -- GRADE-adapted level (high/moderate/low/very_low/"")

HypothesisEvaluated event field:
  certainty_of_evidence  -- carries Director's assessment to frontend

Director evaluation prompt: 6 methodology sections
  <evidence_hierarchy>         -- 8-tier reliability ranking
  <effect_size_thresholds>     -- domain-specific noise floors
  <bayesian_updating>          -- prior → posterior update rules
  <contradiction_resolution>   -- 4-step resolution hierarchy
  <convergence_check>          -- independent method agreement
  <methodology_checks>         -- controls, criteria, analysis plan, confounders

Output format: +2 new fields
  "certainty_of_evidence": "high|moderate|low|very_low"
  "evidence_convergence": "converging|mixed|contradictory"

Orchestrator wiring:
  - Reads certainty_of_evidence from evaluation output
  - Stores on Hypothesis entity
  - Includes in HypothesisEvaluated event
  - Includes in InvestigationCompleted hypothesis dicts
  - Logs evidence_convergence for audit trail
  - Serialized/deserialized in PostgreSQL repository
```

**Key design decisions:**
- Certainty of evidence is a string field on Hypothesis (not an enum) -- Director-assigned, keeps domain layer simple
- Evidence hierarchy is prompt guidance (8 tiers), not infrastructure code -- Director reasons over tiers rather than computing them algorithmically
- Bayesian updating is formalized as multiplier rules in the prompt rather than coded computation -- keeps the LLM as the reasoning engine while providing structured methodology
- Contradiction resolution follows a resolution hierarchy (identity → assay → temporal → severity) rather than averaging -- prevents masking genuine disagreements
- Convergence check is a separate explicit field rather than folded into confidence -- allows the frontend to distinguish "high confidence from one method" vs "moderate confidence from converging methods"

---

### Phase 5: Negative Controls & Model Validation -- UPGRADED

**Status:** Complete. Grounded in 33 verified sources. See [negative-controls.md](../research/methodology/negative-controls.md).

**Sources:**
- Zhang et al. (1999) -- Z-factor / Z' statistic for assay quality separation
- Mysinger et al. (2012) -- DUD-E: property-matched decoys (50 per active, 102 targets)
- Chicco & Jurman (2020) -- MCC superiority over accuracy and F1 for imbalanced datasets
- Truchon & Bayly (2007) -- BEDROC: early-recognition metric for virtual screening
- OECD (2007, 2023) -- 5 Principles for QSAR model validation + Assessment Framework
- Tropsha (2010) -- Best practices for QSAR development, validation, exploitation
- Hanley & McNeil (1982) -- AUROC confidence intervals
- Wallach & Lilien (2011) -- Bias from naive negative control selection
- Cortes-Ciriano & Bender (2019) -- Conformal prediction for applicability domain
- Guo et al. (2024) -- Scaffold splits overestimate VS performance
- + 23 additional verified sources (see research file)

**8 Universal Components (all experts converge on):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | Positive Controls | >= 2 known actives (IC50 < 1 uM) from distinct scaffolds; failure invalidates the run |
| 2 | Property-Matched Negatives | Match actives on MW, cLogP, HBD, HBA, charge (DUD-E criteria); confirmed inactivity from ChEMBL |
| 3 | Calibrated Threshold | No fixed 0.5 cutoff; calibrate via Youden index or MCC maximization on validation set |
| 4 | Assay Quality Score (Z') | Z' = 1 - (3*SD_pos + 3*SD_neg) / \|mean_pos - mean_neg\|; flag Z' < 0.5 |
| 5 | Multi-Metric Reporting | MCC, AUROC, EF1%, BEDROC(alpha=20) minimum; accuracy alone is misleading |
| 6 | Permutation Significance | Y-scrambling (>= 100 permutations); p > 0.05 = model not better than random |
| 7 | Applicability Domain | Max Tanimoto to nearest training compound; Tc < 0.35 = outside AD warning |
| 8 | Scaffold-Split Validation | Bemis-Murcko + clustering splits; report both for honest generalizability assessment |

**Implementation:**
```
PositiveControl entity fields:
  identifier        -- identifier of known active subject
  identifier_type   -- type (smiles, protocol, etc.)
  name              -- display name
  known_activity    -- quantitative activity (e.g. "Ki ~1 nM vs Class A beta-lactamase")
  source            -- provenance justification
  score             -- model prediction score
  expected_active   -- always True (known active)
  correctly_classified  -- property: score >= 0.5

Director formulation prompt:
  Now outputs positive_controls alongside negative_controls
  Guidance: 1-2 positive controls per investigation
  Molecular, training, and nutrition domain examples updated

Director synthesis prompt:
  <validation_quality> section assesses control separation, classification quality
  model_validation_quality field: "sufficient" | "marginal" | "insufficient"
  Insufficient validation downgrades all hypothesis certainty by one level
  +Z'-factor thresholds (>=0.5 excellent, >0 marginal, <=0 unusable)
  +Permutation significance (p < 0.05 = better than random)
  +Scaffold-split gap (>0.15 = memorization risk)

Orchestrator wiring:
  - Phase 3: stores pos_control_suggestions from formulation output
  - Phase 4: captures trained model_ids from train_model tool results
  - Phase 5: scores controls through trained models via predict_candidates
  - Phase 5: computes Z'-factor from positive/negative control scores
  - Phase 5: emits ValidationMetricsComputed event with Z'-factor + quality
  - Phase 5: falls back to score=0.0 if no trained model or non-molecular domain
  - Phase 6: includes validation metrics text (Z'-factor, separation stats) in synthesis context
  - InvestigationCompleted event carries positive_controls list + validation_metrics dict

Validation domain module (investigation/domain/validation.py):
  compute_z_prime(positive_scores, negative_scores) -> AssayQualityMetrics
  Z' = 1 - (3*sigma_pos + 3*sigma_neg) / |mu_pos - mu_neg|
  Thresholds: >= 0.5 excellent, > 0 marginal, <= 0 unusable, insufficient if < 3 per group

PredictionService.train() dual-split metrics:
  Scaffold-split: auroc, auprc, accuracy, f1 (primary, honest generalizability)
  Random-split: random_auroc, random_auprc, random_accuracy, random_f1 (comparison)
  Permutation: permutation_p_value (Y-scrambling, 100 permutations, Phipson & Smyth 2010)

ValidationMetricsComputed domain event → validation_metrics SSE event type
PositiveControlRecorded domain event → positive_control SSE event type
```

**Key design decisions:**
- Positive controls are as important as negative controls -- without them, pipeline failures are undetectable (Zhang et al., 1999)
- Validation quality rating (sufficient/marginal/insufficient) gates certainty assessment -- insufficient validation downgrades all hypothesis certainty
- Property-matching guidance lives in prompts rather than enforced in code -- the Director is responsible for selecting appropriate controls
- `PositiveControl` mirrors `NegativeControl` pattern for consistency -- frozen dataclass with `correctly_classified` property

---

### Phase 6: Synthesis -- UPGRADED

**Status:** Complete. Grounded in 29 verified sources. See [synthesis.md](../research/methodology/synthesis.md).

**Sources:**
- Guyatt et al. (2008) -- GRADE: certainty of evidence (high/moderate/low/very low) with 5 downgrading + 3 upgrading domains
- Cochrane Handbook v6.4 (Higgins et al., 2019/2023) -- Summary of Findings tables, structured synthesis methodology
- PRISMA 2020 (Page et al., 2021) -- 27-item systematic review reporting guideline
- Popay et al. (2006) -- Narrative synthesis guidance (4-element framework for non-meta-analytic synthesis)
- Campbell et al. (2020) -- SWiM: Synthesis without meta-analysis (9-item reporting checklist)
- Derringer & Suich (1980) -- Desirability functions for simultaneous multi-response optimization
- Bickerton et al. (2012) -- QED: desirability-based drug-likeness scoring (8 properties, geometric mean)
- Hwang & Yoon (1981) -- TOPSIS: multi-attribute ranking by distance to ideal solution
- Nicolaou & Brown (2013) -- Pareto optimization in drug design (non-dominated sets, trade-off analysis)
- Peng (2011) -- Reproducibility spectrum in computational science
- Goble et al. (2020) -- FAIR principles for computational workflows
- Ioannidis (2005) -- Systematic factors that make research findings less likely to be true
- Schneider et al. (2020) -- Grand challenges in AI-driven drug design
- Snilstveit et al. (2016) -- Evidence gap maps for identifying knowledge gaps
- + 15 additional verified sources (see research file)

**10 Universal Components (all experts converge on):**

| # | Component | Description |
|---|-----------|-------------|
| 1 | Certainty of Evidence | GRADE-adapted levels (high/moderate/low/very low) per hypothesis and overall; explicit domain reasoning |
| 2 | Structured Narrative Synthesis | Tabulate evidence grouped by hypothesis; SWiM approach (grouping, standardized metrics, heterogeneity) |
| 3 | Multi-Criteria Candidate Ranking | Desirability functions or TOPSIS across all criteria; safety gates as hard cutoffs, then soft scoring |
| 4 | Strength of Recommendation | Priority tiers (1-4) per candidate based on certainty, benefit/risk balance, resource implications |
| 5 | Limitations Disclosure | Structured taxonomy: methodology, data, scope, interpretation; explicitly flag what was NOT tested |
| 6 | Reproducibility Documentation | FAIR workflow: data sources, model parameters, tool sequences, software versions |
| 7 | Knowledge Gap Map | Hypothesis-vs-evidence-type matrix; classify gaps (evidence/quality/consistency/scope/temporal) |
| 8 | Follow-Up Experiment Recommendations | Prioritized next experiments by impact on confidence; distinguish computational from experimental |
| 9 | Summary of Findings Table | Per-hypothesis tabular summary with certainty level, evidence count, effect sizes, interpretation |
| 10 | Model Validation Summary | Aggregate control results + validation metrics + AD coverage into single quality statement |

**Implementation:**
```
Director synthesis prompt: +6 methodology sections
  (CERTAINTY_GRADING, RECOMMENDATION_STRENGTH, LIMITATIONS_TAXONOMY,
   KNOWLEDGE_GAPS, FOLLOW_UP, VALIDATION_QUALITY)

Synthesis output format: structured fields replacing free-text
  - hypothesis_assessments[].certainty (GRADE-adapted level)
  - hypothesis_assessments[].certainty_reasoning (domain reasoning)
  - candidates[].priority (1-4 recommendation tier)
  - limitations[] as {category, description} instead of plain strings
  - knowledge_gaps[] with gap_type classification
  - follow_up_experiments[] with impact and type
  - model_validation_quality (sufficient/marginal/insufficient)

Candidate entity: +priority field (int, 0-4)

Domain configs: priority assignment criteria per domain
  - Molecular: prediction_score + docking_score + ADMET
  - Training: evidence_score + effect_size + confidence
  - Nutrition: evidence_score + effect_size + safety_score
```

**Key design decisions:**
- GRADE framework adapted from clinical medicine to computational discovery (5 downgrading + 3 upgrading domains mapped to computational equivalents)
- Structured narrative synthesis (SWiM) is the appropriate paradigm since Ehrlich combines heterogeneous evidence types that cannot be meta-analyzed
- Four-tier recommendation strength (Priority 1-4) replaces binary advance/don't advance
- Structured limitations taxonomy replaces free-text list for auditability
- Knowledge gap map is a novel addition revealing what evidence is missing
- Desirability scoring guidance in prompts rather than hard-coded computation (Director applies soft reasoning)

## Process

For each phase:
1. Deep research on best practices from top scientists and frameworks
2. Identify universal components that ALL experts agree on
3. Map current implementation gaps
4. Define new entity fields and prompt updates
5. Implement (domain → application → infrastructure → frontend)
6. Update all docs
7. Run full quality gates

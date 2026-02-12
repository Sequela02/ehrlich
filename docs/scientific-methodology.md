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
- `hypothesis_type` spans domains: molecular science uses mechanistic/structural/pharmacological/toxicological; sports science uses physiological/performance/epidemiological. `DomainConfig.hypothesis_types` defines valid types per domain.
- `DomainConfig` serves as the extension point for domain-specific validation and synthesis methodology (Phases 5-6).

---

### Phase 2: Literature Survey -- RESEARCHED

**Status:** Research complete. See [literature-survey-research.md](../research/literature-survey-research.md). Implementation pending.

**Current state:** Basic "search and summarize" via Semantic Scholar.

**Research covers:** Systematic review methodology (PRISMA), search strategies, evidence grading, bias assessment, inclusion/exclusion criteria, rapid scoping review adaptation for AI-driven discovery.

---

### Phase 3: Experiment Design -- RESEARCHED

**Status:** Research complete. See [experiment-design-research.md](../research/experiment-design-research.md). Implementation pending.

**Current state:** Director picks tools and writes a description.

**Research covers:** 20 universal components spanning Fisher's principles (randomization, replication, blocking), variables and controls, statistical power (Cohen), strong inference (Platt), sensitivity analysis (Saltelli), benchmarking methodology (MoleculeNet, SAMPL, TDC), verification vs. validation (Oberkampf), applicability domain (OECD Principle 3), uncertainty quantification, ablation studies, information-theoretic experiment selection, reproducibility (FAIR), negative results reporting.

---

### Phase 4: Evidence Evaluation -- RESEARCHED

**Status:** Research complete. See [evidence-evaluation-research.md](../research/evidence-evaluation-research.md). Implementation pending.

**Current state:** Criteria-based comparison (improved with hypothesis upgrade).

**Research covers:** 20 universal components spanning evidence hierarchies (Burns & Chung), effect sizes (Cohen), confidence intervals (Cumming), weight of evidence (OECD), Bayesian updating (Kass & Raftery, Jeffreys), prediction calibration (Brier, Platt, conformal), multi-source data integration, ensemble consensus, activity cliffs (Maggiora, Stumpfe & Bajorath), retrospective vs. prospective evidence quality, temporal discounting, contradiction resolution, SAR transferability, quantitative confidence aggregation.

---

### Phase 5: Negative Controls & Model Validation -- RESEARCHED

**Status:** Research complete. See [negative-controls-research.md](../research/negative-controls-research.md). Grounded in 33 verified sources. Implementation pending.

**Current state:** Basic pass/fail classification with configurable threshold (default 0.5). Generic `NegativeControl` entity with `identifier`/`score`/`threshold`. No positive controls, no statistical metrics (MCC, AUROC, Z').

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

**Key design decisions:**
- Positive controls are as important as negative controls -- without them, pipeline failures are undetectable
- MCC replaces accuracy as primary classification metric (Chicco & Jurman, 2020 consensus)
- Threshold calibration from data replaces arbitrary 0.5 cutoff
- Z' concept adapted from wet-lab HTS to measure prediction score separation
- Conformal prediction preferred over binary AD methods for compound-specific confidence intervals

---

### Phase 6: Synthesis -- RESEARCHED

**Status:** Research complete. See [synthesis-research.md](../research/synthesis-research.md). Grounded in 29 verified sources. Implementation pending.

**Current state:** Director summarizes all results into a structured report with candidates, hypothesis assessments, negative control summary, and limitations list. No formal certainty grading, no structured candidate ranking method, no knowledge gap analysis.

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

**Key design decisions:**
- GRADE framework adapted from clinical medicine to computational molecular discovery (5 downgrading domains mapped to: model validation quality, method inconsistency, evidence indirectness, imprecision, and database coverage gaps)
- Desirability functions (Derringer-Suich) preferred over hard cutoffs for candidate ranking -- QED demonstrates this works well for drug-likeness
- Structured narrative synthesis (SWiM) is the appropriate paradigm since Ehrlich combines heterogeneous evidence types that cannot be meta-analyzed
- Knowledge gap map is a novel addition: hypothesis-vs-evidence-type matrix revealing what evidence is missing
- Four-tier recommendation strength (Priority 1-4) replaces binary "advance/don't advance"

## Process

For each phase:
1. Deep research on best practices from top scientists and frameworks
2. Identify universal components that ALL experts agree on
3. Map current implementation gaps
4. Define new entity fields and prompt updates
5. Implement (domain → application → infrastructure → frontend)
6. Update all docs
7. Run full quality gates

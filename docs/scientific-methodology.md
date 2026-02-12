# Scientific Methodology

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
  hypothesis_type     -- mechanistic / structural / pharmacological / toxicological
  prior_confidence    -- Bayesian prior (0.0-1.0, set at formulation)
  confidence          -- Bayesian posterior (updated after evaluation)
```

**Key design decision:** Success/failure criteria live on the Hypothesis, not the Experiment. The hypothesis defines WHAT to measure; the experiment defines HOW to measure it. Evaluation compares observations against pre-defined criteria (objective) instead of subjective judgment.

---

### Phase 2: Literature Survey -- TODO

**Current state:** Basic "search and summarize" via Semantic Scholar.

**Research needed:** Systematic review methodology (PRISMA), search strategies, evidence grading, bias assessment, inclusion/exclusion criteria.

---

### Phase 3: Experiment Design -- TODO

**Current state:** Director picks tools and writes a description.

**Research needed:** Experimental design principles (Fisher, Box), variables and controls, statistical power, replication, blinding, confounders.

---

### Phase 4: Evidence Evaluation -- TODO

**Current state:** Criteria-based comparison (improved with hypothesis upgrade).

**Research needed:** Evidence hierarchy (pyramid), meta-analysis principles, effect sizes, confidence intervals, weight of evidence frameworks (GRADE).

---

### Phase 5: Negative Controls -- TODO

**Current state:** Basic pass/fail classification of known-inactive compounds.

**Research needed:** Validation methodology, statistical significance, sensitivity/specificity, ROC analysis, Z-factor for assay quality.

---

### Phase 6: Synthesis -- TODO

**Current state:** Director summarizes all results into a structured report.

**Research needed:** Systematic synthesis (Cochrane), GRADE framework, strength of recommendation, limitations assessment, reproducibility criteria.

## Process

For each phase:
1. Deep research on best practices from top scientists and frameworks
2. Identify universal components that ALL experts agree on
3. Map current implementation gaps
4. Define new entity fields and prompt updates
5. Implement (domain → application → infrastructure → frontend)
6. Update all docs
7. Run full quality gates

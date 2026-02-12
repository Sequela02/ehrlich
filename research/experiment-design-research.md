# Experiment Design Research

Phase 3 of the [Scientific Methodology Upgrade](../docs/scientific-methodology.md).

## Sources

| # | Author/Framework | Year | Key Contribution | Verified |
|---|-----------------|------|------------------|----------|
| 1 | Fisher, R.A. | 1935 | *The Design of Experiments*. Foundational principles: randomization, replication, blocking. | Yes |
| 2 | Cohen, J. | 1988 | *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Power/sample-size benchmarks (80% power, alpha=0.05). | Yes |
| 3 | Box, G.E.P. & Wilson, K.B. | 1951 | Response Surface Methodology. Factorial designs, multi-factor optimization. *JRSS-B*, 13(1), 1-45. | Yes |
| 4 | Platt, J.R. | 1964 | Strong Inference. Crucial experiments that discriminate between competing hypotheses. *Science*, 146(3642), 347-353. DOI: 10.1126/science.146.3642.347 | Yes |
| 5 | Saltelli, A. et al. | 2008 | *Global Sensitivity Analysis: The Primer*. Sobol indices, variance-based SA. Wiley. | Yes |
| 6 | Razavi, S. et al. | 2021 | "The Future of Sensitivity Analysis." *Env. Modelling & Software*, 137, 104954. DOI: 10.1016/j.envsoft.2020.104954 | Yes |
| 7 | Wu, Z. et al. | 2018 | MoleculeNet benchmark. *Chemical Science*, 9(2), 513-530. DOI: 10.1039/c7sc02664a | Yes |
| 8 | Huang, K. et al. | 2021 | Therapeutics Data Commons (TDC). *NeurIPS Datasets and Benchmarks Track*. | Yes |
| 9 | Mobley, D.L. et al. | 2008-present | SAMPL blind prediction challenges: hydration FE, pKa, host-guest, logP. | Yes |
| 10 | Oberkampf, W.L. & Roy, C.J. | 2010 | *Verification and Validation in Scientific Computing*. Cambridge University Press. | Yes |
| 11 | OECD | 2007 | QSAR Validation Principles (5 principles). Principle 3: defined applicability domain. ENV/JM/MONO(2007)2 | Yes |
| 12 | Jaworska, J. et al. | 2005 | QSAR applicability domain estimation by training set projection. *ATLA*, 33(5), 445-459. | Yes |
| 13 | Tropsha, A. | 2010 | Best Practices for QSAR Model Development, Validation, and Exploitation. *Molecular Informatics*, 29, 476-488. | Yes |
| 14 | Sheridan, R.P. | 2013 | Time-split cross-validation for prospective prediction. *JCIM*, 53(4), 783-790. DOI: 10.1021/ci400084k | Yes |
| 15 | Lindley, D.V. | 1956 | Information measure for experiment selection. *Annals of Mathematical Statistics*, 27, 986-1005. | Yes |
| 16 | Chaloner, K. & Verdinelli, I. | 1995 | Bayesian Experimental Design: A Review. *Statistical Science*, 10(3), 273-304. DOI: 10.1214/ss/1177009939 | Yes |
| 17 | Wilkinson, M.D. et al. | 2016 | FAIR Guiding Principles for data stewardship. *Scientific Data*, 3, 160018. DOI: 10.1038/sdata.2016.18 | Yes |
| 18 | Fanelli, D. | 2012 | "Negative results are disappearing." *Scientometrics*, 90(3), 891-904. DOI: 10.1007/s11192-011-0494-7 | Yes |
| 19 | Newell, A. | 1975 | Origin of "ablation" in AI: removing system components to measure contribution. In *Speech Recognition* (ed. Reddy), Academic Press. | Yes |
| 20 | Collberg, C. & Proebsting, T. | 2016 | Reproducibility in Computer Science (code availability study). *CACM*, 59(3), 62-69. | Yes |

## Part A: Traditional Experiment Design Principles

### 1. Fisher's Three Principles (1935)

Sir Ronald A. Fisher laid the foundations of experimental design with three key principles:

**Randomization.** Randomly assign treatments to experimental units to avoid systematic bias. Randomization "averages out the effects of uncontrolled (lurking) variables." In computational terms: shuffle the order of trials so confounding factors (data source order, API response timing) don't align with any particular treatment.

**Replication.** Perform independent repetitions to estimate variability. Fisher noted that "replication enables the experimenter to obtain an estimate of experimental error." In a docking study, this means running simulations with different random seeds or on different protein targets. Re-running a deterministic computation with identical inputs is *repetition* (yields no new information), not *replication*.

**Blocking.** Group similar experimental units to control known sources of variability. For example, batch-to-batch differences or hardware variations can be "blocked" by ensuring each block contains all treatment combinations. In code, this means processing data in batches (blocks) so each batch has a mix of all conditions.

**Operationalization for AI Agent:**
- Schedule computational experiments in random order
- Replicate analyses across independent data splits or random seeds (minimum 5 replicates for meaningful statistics)
- Group runs (blocks) to account for known differences in data sources or compute environments

### 2. Variables and Controls

A rigorous experiment clearly defines:
- **Independent variable**: the factor you manipulate (scoring function, hyperparameters, compound library)
- **Dependent variable**: the outcome you measure (binding affinity, model accuracy, enrichment factor)
- **Confounding variable**: extraneous factor influencing both (protein size, dataset difficulty, chemical series)

**Controls establish baselines and check validity:**

| Control Type | Wet-Lab | In Silico Equivalent |
|-------------|---------|---------------------|
| Negative control | No treatment / neutral input | Random-guess model, shuffled labels, known-inactive compounds |
| Positive control | Known effective treatment | Known binder/active compound, gold-standard algorithm |
| Vehicle control | Solvent without active compound | Model with randomized features (ensures no phantom signal) |

**Operationalization:** The AI agent should automatically include baseline models (negative controls) and benchmark cases (positive controls) in every experiment batch.

### 3. Statistical Power and Sample Size (Cohen, 1988)

Statistical power is the probability of detecting a true effect. It depends on effect size, sample size, and significance threshold.

- **Convention:** 80% power at alpha = 0.05
- **Meaning:** 80% chance of detecting a real effect if it exists
- **Rule:** "The larger the sample size, the easier it is to detect smaller effects"

**Operationalization:** Before running large experiments, estimate required sample size. For ML model comparison, compute how many test examples are needed to reliably distinguish two models with a given effect size. Run a quick pilot to estimate effect variance, then set final sample size.

### 4. Replication vs. Repetition

| | Replication | Repetition |
|--|------------|------------|
| Definition | Repeat entire experiment independently (new samples, new runs) | Repeat measurement on same sample |
| Information | Provides independent estimate of variability | No new information if deterministic |
| In silico | Different random seeds, different data splits, different targets | Same inputs, same seed |
| Value | Estimates "experimental error" | Confirms code stability (repeatability) |

**Operationalization:** For ML models, train with 5+ different random seeds and report mean +/- SD. These are replicates. Running one training run twice without changing seed or data is just repetition.

### 5. Confounders and Bias

A confounder is "a third variable that influences both the independent and dependent variables." If not controlled, confounders bias estimates of causal effects.

**Methods to control confounders:**
1. **Randomization** (gold standard): equalizes confounders on average across groups
2. **Matching**: pair similar samples
3. **Restriction**: limit scope so confounder is constant
4. **Statistical control**: include confounders as covariates in regression

**Experimental biases to prevent:**
- Selection bias: randomize case ordering
- Data dredging / p-hacking: pre-specify analyses
- HARKing: register hypotheses before running experiments
- Confirmation bias: design experiments that can falsify, not just confirm

### 6. Blinding

Blinding prevents subjective bias by hiding information from participants, researchers, or analysts.

| Design | Who is Blinded | In Silico Equivalent |
|--------|---------------|---------------------|
| Single-blind | Subjects | Agent doesn't see ground truth during optimization |
| Double-blind | Subjects + experimenters | Neither algorithm nor evaluation metric exposed until after predictions |

**Key computational examples:**
- **CASP challenges**: protein structure prediction; neither participants nor assessors know the true structure until after submissions
- **SAMPL challenges**: binding affinity predictions submitted before experimental results are released
- **Hold-out test sets**: agent cannot query labels during model training

**Operationalization:** The AI agent should not have access to ground truth labels during prediction. Evaluation metrics should be hidden until after decisions are made. This prevents overfitting to known answers.

### 7. Factorial and Efficient Designs (Box & Wilson, 1951)

Testing one variable at a time is inefficient. Factorial designs vary multiple factors simultaneously, measuring all combinations.

- **Full factorial**: test all combinations of factor levels (e.g., 2 scoring functions x 3 thresholds = 6 runs)
- **Response Surface Methodology** (Box & Wilson, 1951): build quadratic models to locate optima when multiple inputs vary
- **Advantages**: efficiency (same runs estimate multiple effects), detects interactions

**Operationalization:** Instead of tuning one hyperparameter at a time, use factorial or grid designs to systematically explore joint effects. For example, a 3x3 grid over learning rate and batch size explores 9 combinations simultaneously.

### 8. Sequential and Adaptive Experimentation

Traditional designs fix everything up-front. Sequential/adaptive designs adjust based on early results:

- **Group sequential**: analyze at intervals, stop early for clear success or futility
- **Bayesian adaptive**: update beliefs after each batch, choose next experiments to maximize information or expected improvement
- **Multi-armed bandits**: allocate more trials to promising arms while still exploring

**Operationalization:** The AI agent should specify rules for when to stop early or reallocate resources (e.g., if one hypothesis is clearly supported/refuted after initial batches). Requires alpha-spending rules or Bayesian decision thresholds.

### 9. Pre-registration and Analysis Plans

Pre-registration means documenting hypotheses, variables, sample size, and analysis methods *before* data collection. It prevents p-hacking and HARKing.

**Operationalization:** The AI agent should generate a protocol specifying:
- Which experiments will run
- Which metrics will be computed
- How results will be tested (statistical test, alpha level, effect size threshold)
- Decision criteria for hypothesis support/refutation

This protocol must be fixed before running experiments. Any deviations must be noted explicitly. For autonomous AI research, pre-registration can be automated: the planning module writes the protocol before launching simulations.

## Part B: Computational-Specific Design Principles

### 10. Crucial Experiments and Strong Inference (Platt, 1964)

Strong inference accelerates scientific progress by designing experiments that **discriminate between competing hypotheses** rather than confirming one.

**The method:**
1. Devise alternative hypotheses -- don't settle on one explanation
2. Design crucial experiments -- different outcomes exclude specific hypotheses
3. Execute for clean results -- get unambiguous data
4. Iterate -- refine remaining possibilities and repeat

**Computational molecular discovery examples:**
- "Activity driven by hydrogen bonding" vs. "hydrophobic interactions" -- train single-feature models to discriminate
- "Model A outperforms Model B on scaffold-split data" -- direct head-to-head comparison
- "Binding at site A" vs. "site B" -- dock at both sites, compare scores

**Operationalization:**
- When multiple mechanistic explanations exist for bioactivity, design a computational experiment that produces different outcomes depending on which hypothesis is true
- Prioritize experiments by information gain: run the experiment that rules out the most hypotheses
- Avoid confirmatory bias: design experiments that can *falsify*, not just confirm

### 11. Sensitivity Analysis and Robustness (Saltelli, 2008; Razavi et al., 2021)

Sensitivity analysis quantifies how model outputs change when inputs/parameters vary. Robustness measures whether conclusions hold under different conditions.

**Types:**
- **Local (one-at-a-time)**: vary one parameter, hold others fixed. Fast but misses interactions.
- **Global (variance-based)**: Sobol indices partition variance across all parameters. Identifies main effects + interactions. Computationally expensive but robust.

**Molecular science fragility examples:**
- Docking: results change dramatically with grid box placement (+/-2 Angstrom), scoring function choice, protonation state
- QSAR: predictions flip with different train/test splits, descriptor cutoffs, hyperparameter choices

**Robustness indicators:**
- Consistent top-ranked poses across multiple docking programs
- Consistent predictions across multiple CV folds, featurization schemes, algorithm ensemble

**Operationalization:**
- Run perturbation tests on critical parameters (+/-10%, +/-20%)
- Flag high-sensitivity results: if changing random seed alters top predictions, mark as FRAGILE
- Report robustness metrics: "Accuracy = 0.85 +/- 0.03 across 10 random seeds" not just "Accuracy = 0.85"

### 12. Benchmarking Methodology (MoleculeNet, SAMPL, TDC)

Invalid benchmarks mislead about model performance. Computational methods can overfit to benchmark characteristics.

**Valid benchmarking requires:**
1. **Representative test set**: matches future deployment conditions
2. **Scaffold splits** (Wu et al., 2018): separates structurally different molecules, prevents data leakage
3. **Temporal splits** (Sheridan, 2013): train on old data, test on new; mimics real discovery
4. **External validation**: test on completely independent dataset from different source
5. **Negative control baselines**: random classifier, constant predictor, simple linear model

**Misleading benchmark signs:**
- Random splits (inflates performance via data leakage from similar molecules)
- Cherry-picked datasets (only easy/clean examples)
- Metric misalignment (optimizing accuracy when enrichment matters)
- No "dumb baseline" comparison

**Operationalization:**
- Always specify split type (scaffold/temporal/random) with justification
- Always include at least one negative control baseline
- Use multiple test sets: internal, external, adversarial
- If proposed model performs worse than simple baseline, flag as error

**Key benchmarks:**
| Benchmark | Type | Strengths |
|-----------|------|-----------|
| MoleculeNet (Wu et al., 2018) | Retrospective | 700K+ compounds, multiple splits, diverse endpoints |
| SAMPL Challenges (Mobley et al.) | Prospective blind | Predictions before experimental results; prevents overfitting |
| TDC (Huang et al., 2021) | Real-world | Distribution shifts, temporal splits, ADMET + generation tasks |

### 13. Verification vs. Validation (Oberkampf & Roy, 2010)

A critical distinction unique to computational science:

| | Verification | Validation |
|--|-------------|------------|
| Question | "Are we solving the equations right?" | "Are we solving the right equations?" |
| Concerns | Code correctness, numerical accuracy, implementation bugs | Model adequacy, physical realism, predictive accuracy |
| Example (wrong) | "Code runs without errors" | "Model fits training data well" |
| Example (correct) | "Same results across implementations" | "Predicts held-out experimental data accurately" |

**Verification checklist (before trusting results):**
- Numerical checks: energy conservation, gradient accuracy, convergence with increased sampling
- Reproducibility: same seed -> identical results; different implementations -> same answer
- Unit tests: test on molecules with known answers, check limiting cases

**Validation checklist (before deploying model):**
- External validation: test on data from different source/chemical series
- Prospective validation: make predictions BEFORE experiments
- Physical consistency: results obey known laws, properties in reasonable ranges

**Operationalization:** Always verify computational correctness *before* validating model predictions. A model that gives wrong answers due to a bug is not validated even if its scores look good on paper.

### 14. Applicability Domain (OECD Principle 3; Tropsha, 2010; Jaworska et al., 2005)

The Applicability Domain (AD) defines the chemical/biological space where a model's predictions are reliable. **Outside the AD = extrapolation = unreliable.**

**OECD Principle 3:** "A defined domain of applicability" -- one of 5 required QSAR validation principles.

**The problem:** Models trained on X give numbers for Y, but those numbers are meaningless extrapolation. A QSAR model trained on aromatic compounds gives garbage predictions for aliphatic compounds -- but it still returns a number.

**Methods to define AD:**
1. **Descriptor-based distance**: Mahalanobis/Euclidean distance to training set centroid; threshold determines inside/outside
2. **Leverage-based (Hat matrix)**: warning threshold h* = 3p/n; high leverage = high influence point
3. **Ensemble disagreement**: multiple models agree -> inside AD; models disagree -> outside AD
4. **Nearest-neighbor distance**: distance to closest training compound

**Operationalization:**
- Always check AD before reporting a prediction
- Report confidence qualifier: HIGH (inside AD), MODERATE (near boundary), LOW (outside AD -- extrapolation)
- When outside AD: warn user, suggest acquiring data in that chemical space, do not trust for high-stakes decisions

### 15. Uncertainty Quantification

Report **how certain** predictions are, not just the predictions themselves.

**Two types:**
- **Aleatoric**: irreducible noise in data (measurement error). Cannot be reduced by more training data.
- **Epistemic**: reducible uncertainty from limited knowledge (small training set). Can be reduced with more data.

**Methods:**
| Method | How | Cost |
|--------|-----|------|
| Prediction intervals | Bootstrap or theory-based CI | Low |
| Ensemble disagreement | Train N models, report mean +/- SD | Moderate |
| Conformal prediction | Distribution-free intervals with guaranteed coverage | Moderate |
| Bayesian methods | Posterior distribution over parameters (GP, BNN) | High |

**Why it matters:**
- Without UQ: "Compound A IC50 = 10 nM" -> prioritize A
- With UQ: "Compound A IC50 = 10 +/- 500 nM (novel scaffold)" vs. "Compound B IC50 = 50 +/- 5 nM (known scaffold)" -> prioritize B (more reliable)

**Operationalization:**
- Always use ensemble methods (bootstrap, cross-validation, multiple algorithms)
- Report uncertainty alongside every prediction
- Flag high-uncertainty predictions for experimental validation priority
- Use uncertainty for active learning: propose experiments that reduce uncertainty most

### 16. Ablation Studies (Newell, 1975)

Systematically remove components to understand what drives results. If performance doesn't drop when you remove something, it wasn't important.

The term "ablation" in AI was coined by Allen Newell (1975) by analogy with ablation in neuroscience (lesion studies).

**Components to ablate in molecular ML:**
- Molecular descriptors / features
- Model architecture elements (layers, attention heads)
- Data augmentation techniques
- Preprocessing steps
- Feature selection methods

**Example:**
```
Full GNN model:        R2 = 0.85
Remove attention:      R2 = 0.84 (-0.01)  -> Minor, can remove
Remove bond features:  R2 = 0.78 (-0.07)  -> Important, keep
Remove 3rd MP layer:   R2 = 0.85 ( 0.00)  -> Redundant, remove
Remove charge features: R2 = 0.72 (-0.13)  -> Critical, keep
```

**Operationalization:**
- After model development: which innovations actually helped?
- Before deployment: can we simplify without losing performance?
- For interpretability: what does the model rely on?
- Report: critical components (delta > 5%), minor (1-5%), redundant (< 1%)

### 17. Information-Theoretic Experiment Selection (Lindley, 1956; Chaloner & Verdinelli, 1995)

Choose the experiment that reduces uncertainty the most. Measure information gain using Expected Information Gain (EIG):

**EIG(d) = E[KL(P(theta|y,d) || P(theta))]** = Expected reduction in uncertainty

**Strategies ranked by efficiency:**
1. **Expected Information Gain** (best but expensive): pick experiments that maximally reduce overall uncertainty across entire compound space
2. **Uncertainty sampling** (good approximation): pick compounds where model is most uncertain
3. **Random/diverse sampling** (simple): adequate when budget is large

**Result:** Strategy 1 typically requires 2-3x fewer experiments than random selection to achieve same accuracy.

**Operationalization:**
- For small experimental budgets (< 100 compounds): use EIG or uncertainty sampling
- For medium budgets (100-1000): uncertainty sampling
- For large budgets (> 1000): random or diversity-based sampling is adequate
- Report expected uncertainty reduction vs. random selection as efficiency metric

### 18. Reproducibility and Provenance (Wilkinson et al., 2016; Collberg & Proebsting, 2016)

**FAIR Principles** (Findable, Accessible, Interoperable, Reusable) apply to all computational research outputs.

**Computational reproducibility requires:**
1. **Code versioning**: exact commit hash, tagged releases
2. **Data versioning**: data hashes, preprocessing scripts, train/test splits with seeds
3. **Environment**: package versions, random seeds for all stochastic methods
4. **Workflow provenance**: which computations ran, in what order, with what parameters

**Molecular science-specific standards:**
- Chemical structures: canonical SMILES, InChI, PubChem CID, ChEMBL ID
- Bioactivity data: specified units (nM, uM, pIC50), assay details, replicates
- Computational details: software name/version/citation, force field version, all non-default parameters

**Operationalization:** The AI agent should log every parameter, random seed, software version, data source, and preprocessing step for every experiment. Same inputs + same environment must produce same outputs.

### 19. Negative Results and Null Findings (Fanelli, 2012)

Publication bias hides negative results, creating false confidence. Fanelli (2012) showed positive-result papers increased from ~70% (1990) to >85% (2007).

**Why negative results matter for Ehrlich:**
- Avoid wasted effort: if an approach failed, don't retry it
- Prevent false positives: seeing only positive results inflates confidence
- Learn mechanistic insights: "why didn't this work?" constrains hypothesis space
- Inform future designs: knowing what doesn't work is as valuable as knowing what does

**Computational negative results:**
- "GNN did NOT improve over Random Forest on this dataset"
- "Docking failed to identify known binders (poor negative control)"
- "QSAR model did NOT generalize to new scaffold"
- "Compound predicted as active but was inactive in validation"

**Operationalization:**
- Record ALL experiments, not just successful ones
- Diagnose failure reasons and log them
- Analyze failure patterns across the investigation
- Update priors based on negative results (Bayesian updating)
- Don't repeat failed approaches (maintain a "tried and failed" list)

## Universal Components (Merged: 20 Components)

### Traditional Experiment Design (Fisher-style)

| # | Component | Key Principle | Reference |
|---|-----------|--------------|-----------|
| 1 | Clear Variables & Hypothesis | Explicitly define independent/dependent variables and the hypothesis to test | Fisher (1935) |
| 2 | Controls | Negative/positive/vehicle controls to establish baselines and validate methods | Fisher (1935) |
| 3 | Randomization | Randomly assign or order conditions to prevent systematic bias | Fisher (1935) |
| 4 | Replication | Independent replicates (different seeds/data) to estimate variability; not mere repetition | Fisher (1935) |
| 5 | Blocking/Stratification | Group by known nuisance factors (data source, hardware) to reduce unexplained variance | Fisher (1935) |
| 6 | Blinding | Mask information (hidden test data, double-blind protocols) to avoid bias | CASP, SAMPL |
| 7 | Power & Sample-Size Planning | A priori power analysis to ensure enough runs to detect expected effects (~80% power) | Cohen (1988) |
| 8 | Pre-specified Analysis | Pre-register methods and decision criteria before running experiments | Fisher (1935), AsPredicted |
| 9 | Factorial/Optimal Design | Explore multiple factors and interactions efficiently in fewer runs | Box & Wilson (1951) |
| 10 | Confounder Control | Identify and neutralize confounders via randomization, matching, or statistical control | Fisher (1935) |

### Computational-Specific Design

| # | Component | Why Computational Science Needs It | Reference |
|---|-----------|-----------------------------------|-----------|
| 11 | Hypothesis Discrimination | Efficiently rule out competing explanations, not just confirm one | Platt (1964) |
| 12 | Sensitivity Analysis | Determine if results depend on arbitrary parameter choices | Saltelli (2008), Razavi et al. (2021) |
| 13 | Benchmark Validity | Test sets must match deployment conditions; scaffold/temporal splits | Wu et al. (2018), Sheridan (2013) |
| 14 | Verification vs. Validation | Distinguish "correct computation" from "correct model" | Oberkampf & Roy (2010) |
| 15 | Applicability Domain | Models trained on X cannot predict Y; detect and flag extrapolation | OECD (2007), Tropsha (2010), Jaworska et al. (2005) |
| 16 | Uncertainty Quantification | Report prediction intervals, not point estimates; distinguish aleatoric vs. epistemic | Ensemble methods, conformal prediction |
| 17 | Ablation Studies | Identify which model components actually contribute to performance | Newell (1975) |
| 18 | Information-Theoretic Selection | Choose experiments that maximally reduce uncertainty | Lindley (1956), Chaloner & Verdinelli (1995) |
| 19 | Reproducibility & Provenance | Computational experiments must be exactly reproducible; FAIR principles | Wilkinson et al. (2016) |
| 20 | Negative Results Reporting | Log all experiments; analyze failure patterns; update priors from failures | Fanelli (2012) |

## Key Differences: Wet-Lab vs. Computational Experiments

| Dimension | Traditional Wet-Lab | Computational |
|-----------|-------------------|---------------|
| Execution | Physical manipulation | Simulation / prediction |
| Results | Noisy measurements | Deterministic (given seeds) |
| Goal | Causal inference | Model selection, hypothesis discrimination, domain exploration |
| Limiting factors | Time, cost, physical constraints | Compute time, algorithm scaling, model validity |
| Primary risk | Experimenter bias | Model misspecification, code errors, numerical instability |
| Randomization concern | Essential for confound control | Determinism (given seed) replaces randomization |
| Hypothesis space | One experiment at a time | Can explore exhaustively (if tractable) |

## Mapping to Ehrlich's Current Implementation

| Component | Current State | Gap |
|-----------|--------------|-----|
| Clear Variables & Hypothesis | Hypothesis entity with prediction, null_prediction, criteria | Good -- needs experiment-level variable tracking |
| Controls | `record_negative_control` tool for known-inactive compounds | Needs positive controls and vehicle controls |
| Randomization | Not currently tracked | Director should randomize experiment order |
| Replication | Not currently tracked | Need multiple random seeds per experiment |
| Blocking | Not applicable (single compute environment) | Low priority |
| Blinding | Not applicable (no human evaluators) | Partially inherent: agent doesn't have answer key |
| Power & Sample Size | Not planned | Low priority for rapid scoping review |
| Pre-specified Analysis | Hypothesis has success/failure_criteria | Good -- experiment entity needs pre-specified analysis plan |
| Factorial Design | Not structured | Director could design multi-factor experiments |
| Confounder Control | Not tracked | Director should identify potential confounders |
| Hypothesis Discrimination | Already part of strong inference approach | Good -- Director formulates competing hypotheses |
| Sensitivity Analysis | Not performed | Researcher should run perturbation tests |
| Benchmark Validity | Not structured | Need scaffold/temporal split awareness in ML training |
| Verification vs. Validation | Not distinguished | Researcher should verify tool correctness before trusting results |
| Applicability Domain | Not checked | ML predictions need AD assessment |
| Uncertainty Quantification | Not reported | Ensemble predictions should report mean +/- SD |
| Ablation Studies | Not performed | Optional for complex models |
| Info-Theoretic Selection | Not used | Director could prioritize experiments by information gain |
| Reproducibility & Provenance | SQLite event persistence tracks full timeline | Good -- need parameter/seed logging per experiment |
| Negative Results | `REFUTED` hypothesis status; all experiments logged | Good -- need structured failure analysis |

## Ehrlich's Experiment Design Mode

Given that Ehrlich operates as a **rapid scoping review** (see [literature survey research](literature-survey-research.md)), not all 20 components are equally critical. The following are prioritized by impact:

**High Priority (implement in prompts):**
- Hypothesis Discrimination (Platt) -- already partially implemented
- Controls (positive + negative) -- extend current negative control system
- Pre-specified Analysis -- already partially implemented via success/failure criteria
- Applicability Domain -- critical for ML prediction trustworthiness
- Uncertainty Quantification -- critical for candidate ranking
- Negative Results Reporting -- already partially implemented via REFUTED status
- Sensitivity Analysis -- Director should instruct perturbation tests

**Medium Priority (prompt guidance):**
- Benchmark Validity -- Director should specify split type
- Verification vs. Validation -- Researcher should verify before trusting
- Reproducibility & Provenance -- extend event logging with parameters/seeds
- Confounder Control -- Director should identify confounders
- Replication -- multiple seeds for stochastic experiments

**Low Priority (documented but not enforced):**
- Factorial Design -- complex for autonomous agent
- Power & Sample Size -- less applicable to rapid review
- Blocking/Stratification -- single compute environment
- Blinding -- partially inherent
- Information-Theoretic Selection -- complex for current architecture
- Ablation Studies -- only relevant for complex model architectures

## Corrections and Flags

1. **ChatGPT citation quality**: The ChatGPT research (research/chatgpt.md) cited only website domains (scribbr, wikipedia, jmp) without specific DOIs or paper references. All foundational claims have been cross-referenced with original sources in the Sources table above.

2. **Collberg et al. mischaracterization**: The ChatGPT file stated "Collberg et al. note, reproducibility often means controlling random seeds." The actual Collberg & Proebsting (2016) study was about code availability and execution, not about random seed control specifically. The random seed point is valid but should not be attributed to Collberg. Corrected above.

3. **Newell (1975) ablation attribution**: Verified. Allen Newell coined "ablation" in AI in his 1975 tutorial on speech understanding systems, by analogy with ablation in neuroscience. Confirmed via Wikipedia and multiple academic sources.

4. **All 20 references verified**: Every source in the Sources table has been independently verified via web search. No fabrications detected in either source document.

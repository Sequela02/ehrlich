# Literature Survey Methodology Research

Phase 2 of the [Scientific Methodology Upgrade](../../docs/scientific-methodology.md).

## Sources

| Author/Framework | Year | Key Contribution | Verified |
|-----------------|------|------------------|----------|
| PRISMA (Moher et al.) | 2009 | 27-item checklist for transparent systematic review reporting | Yes |
| PRISMA 2020 (Page et al.) | 2021 | Updated checklist with automation and search documentation emphasis | Yes |
| Cochrane Handbook (Higgins et al.) | 2024 | Gold standard protocol for systematic reviews | Yes |
| PICO (Richardson et al.) | 1995 | Structured question decomposition: Population, Intervention, Comparison, Outcome | Yes |
| Oxford CEBM Levels (Howick et al.) | 2011 | Formal evidence hierarchy by study design | Yes |
| Sackett et al. | 1989 | Original evidence-based medicine hierarchy | Yes |
| Egger et al. | 1997 | Funnel plots and regression test for publication bias | Yes |
| Wohlin | 2014 | Snowballing (citation chasing) as systematic search complement | Yes |
| Canadian Task Force | 1979 | First formal evidence grading hierarchy | Yes |
| OECD QSAR Validation | 2004/2014 | 5 principles for computational prediction credibility | Yes |
| Mobley & Gilson | 2017 | Binding free energy prediction accuracy limits (1-2 kcal/mol) | Yes |
| Ioannidis | 2005 | "Why Most Published Research Findings Are False" (reproducibility) | Yes |
| Begley & Ellis | 2012 | Only 6/53 preclinical studies reproduced (Nature) | Yes |
| Arksey & O'Malley | 2005 | Scoping review 6-stage framework | Yes |
| Levac et al. | 2010 | Refinement of Arksey & O'Malley scoping framework | Yes |
| Tricco et al. | 2018 | PRISMA-ScR: 20-item scoping review checklist | Yes |
| Cochrane Rapid Reviews | 2020 | 26 recommendations for rapid review shortcuts | Yes |
| PECO (Morgan et al.) | 2018 | Population, Exposure, Comparator, Outcome for toxicology | Yes |
| Marshall & Wallace | 2019 | Systematic review automation, ML-assisted screening | Yes |
| Greenhalgh & Peacock | 2005 | Only 30% of sources from protocol searches; 51% from snowballing (BMJ) | Yes |
| GRADE (Guyatt et al.) | 2008 | 4-level evidence quality grading (high/moderate/low/very low). 100+ orgs use it. | Yes |
| AMSTAR 2 (Shea et al.) | 2017 | 16-item checklist for quality of systematic reviews. 7 critical domains. (BMJ) | Yes |
| Navigation Guide (Woodruff & Sutton) | 2014 | Systematic review for environmental health. Bridges clinical SR + IARC. | Yes |
| OHAT (NTP) | 2015/2019 | 7-step SR framework for health assessments. Risk-of-bias tool, 6 domains. | Yes |
| SAMPL Challenges (Mobley et al.) | 2008-present | Blind prediction challenges for computational chemistry (free energy, pKa, logP) | Yes |
| CASP | 1994-present | Critical Assessment of Structure Prediction. Biennial blind protein structure benchmark. | Yes |
| ToxRTool (Schneider et al.) | 2009 | EU toxicological data reliability tool. Binary scoring, Klimisch categories. | Yes |
| ASReview (van de Schoot et al.) | 2021 | Open-source active learning screening. Published in Nature Machine Intelligence. | Yes |
| RAISE (Cochrane/Campbell/JBI) | 2025 | Responsible AI in Evidence Synthesis. Joint position statement + 3-paper guidance. | Yes |

## Frameworks

### PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses)

27-item checklist and flow diagram ensuring transparency. Key requirements:
- Pre-specify objectives and methods (including search strategy)
- Log each search query, number of records retrieved, reasons for exclusion
- Document how many papers included/excluded at each stage (flow diagram)
- Report results completely

**Operationalization:** The AI agent logs every query string, result count, filter applied, and exclusion reason. Output a structured "PRISMA record" (JSON) tracking the funnel from initial hits to final included papers.

**Citations:** Moher et al. (2009) https://pubmed.ncbi.nlm.nih.gov/19621072/ ; Page et al. (2021) https://pubmed.ncbi.nlm.nih.gov/33782057/

### Cochrane Standards

Cochrane reviews follow rigorous protocols emphasizing:
- Pre-specified eligibility criteria
- Comprehensive search across multiple databases to minimize bias
- Explicit protocol (PICO elements + study types) defined before searching
- Search multiple databases, trial registries, gray literature
- "Identify as much relevant evidence as possible"

**Operationalization:** The agent uses a config/protocol (JSON) specifying PICO elements before searching. It iterates through multiple sources (Semantic Scholar, PubMed) using the same query logic. Loops until new sources stop yielding unique results.

**Citation:** Higgins et al., Cochrane Handbook (2024) https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04

### Search Strategy Design (Boolean + Controlled Vocabularies)

- Define main concepts (via PICO), gather synonyms and subject headings for each
- Within each concept: OR together synonyms
- Between concepts: AND the sets
- Include controlled vocabularies (MeSH for biomedical, other ontologies per domain)
- Augment with snowballing (citation chasing) -- backward (references) and forward (citing papers)

**Operationalization:** The agent programmatically constructs Boolean queries from PICO components. Uses APIs to fetch ontology terms (e.g., NCBI MeSH API). Follows citation chains via Semantic Scholar references/citations endpoints with a depth or stopping rule.

**Citation:** Wohlin (2014) https://www.wohlin.eu/ease14.pdf

### Inclusion/Exclusion Criteria

- Rules defined BEFORE searching (in protocol)
- Based on PICO question and study design
- Applied uniformly to every record
- Automation can flag and exclude ineligible records programmatically

**Operationalization:** Criteria encoded as filters on metadata (study type, date, language) and content (keywords in abstract). Fixed in protocol config. Agent applies them consistently to each returned record.

**Citation:** Cochrane Handbook Ch. 3 https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-03

### Evidence Grading

Classic hierarchy (highest to lowest):
1. Systematic reviews / meta-analyses
2. Randomized controlled trials (RCTs)
3. Cohort studies
4. Case-control studies
5. Case series / case reports
6. Expert opinion / in vitro / computational

**Operationalization:** Classify study design from publication type metadata or abstract terms. Assign provisional evidence level. Weight conclusions by evidence strength.

**Citations:** Sackett et al. (1989); Oxford CEBM (Howick et al., 2011) https://www.cebm.net/wp-content/uploads/2014/06/CEBM-Levels-of-Evidence-2.1.pdf

### Bias Assessment

- **Publication bias:** Mitigate by including gray literature (preprints, registries). Detect via funnel plots or Egger's regression.
- **Selection bias:** Reduced by strictly applying pre-specified criteria.
- **Reporting bias:** Flag if registry entry lacks results that publication reports.

**Operationalization:** Include preprint servers in search. Run Egger's test on collected effect sizes if doing meta-analysis. Compare registry entries to published outcomes.

**Citation:** Egger et al. (1997) https://pubmed.ncbi.nlm.nih.gov/9310563/

### PICO Framework

Population, Intervention, Comparison, Outcome -- guides question formulation and search term generation.

**Operationalization:** Parse or receive PICO-structured query. Generate terms for each dimension. Apply Boolean strategy. Ensures search stays on-topic.

**Citation:** Richardson et al. (1995)

### Greenhalgh & Peacock (2005) -- Search Method Effectiveness

Landmark BMJ study auditing 495 primary sources in a systematic review of complex evidence:
- **Only 30%** of sources came from protocol-defined database/hand searches
- **51%** were identified by snowballing (references of references)
- **24%** came from personal knowledge or contacts

**Key insight:** Systematic reviews of complex evidence CANNOT rely solely on protocol-driven database searches. Multiple strategies are essential.

**Operationalization:** The agent must use at least 3 search strategies: (1) database queries, (2) citation chasing (backward + forward), (3) related-paper recommendations. Budget time for each.

**Citation:** Greenhalgh & Peacock (2005) BMJ 331:1064-5. https://pubmed.ncbi.nlm.nih.gov/16230312/

### GRADE Framework

Grading of Recommendations, Assessment, Development, and Evaluation. Used by 100+ organizations including WHO, NICE, Cochrane.

4-level evidence quality rating applied to a BODY of evidence (not individual studies):
- **High:** Further research very unlikely to change confidence in estimate
- **Moderate:** Further research likely to have important impact
- **Low:** Further research very likely to have important impact
- **Very Low:** Any estimate very uncertain

5 factors that can DOWNGRADE quality:
1. Risk of bias
2. Inconsistency (heterogeneity across studies)
3. Indirectness (applicability to question)
4. Imprecision (wide confidence intervals)
5. Publication bias

3 factors that can UPGRADE quality:
1. Large effect size
2. Dose-response gradient
3. All plausible confounders would reduce effect

**Operationalization:** After collecting evidence, the agent rates overall body quality per GRADE dimensions. Outputs a GRADE assessment (high/moderate/low/very low) with justification for each downgrade/upgrade.

**Citation:** Guyatt et al. (2008) BMJ 336:924-6. https://pmc.ncbi.nlm.nih.gov/articles/PMC2335261/

### AMSTAR 2 -- Quality of Systematic Reviews

16-item checklist for assessing the quality of systematic reviews themselves. Generates confidence rating (high/moderate/low/critically low).

7 critical domains:
1. Prior protocol registered
2. Comprehensive literature search
3. Justification for excluding studies
4. Risk of bias assessment for individual studies
5. Appropriate meta-analytical methods
6. Risk of bias considered when interpreting results
7. Publication bias assessed

**Operationalization:** The agent can self-assess its own literature survey against AMSTAR 2 domains. Reports which critical domains are satisfied and which are not. Useful for transparency.

**Citation:** Shea et al. (2017) BMJ 358:j4008. https://pubmed.ncbi.nlm.nih.gov/28935701/

### Navigation Guide (Environmental Health)

Systematic review methodology bridging clinical SR methods with IARC (International Agency for Research on Cancer) approach. Specifically designed for environmental health questions.

Key features:
- Pre-specified protocol
- PECO-based question formulation
- Integrates human, animal, AND mechanistic evidence streams
- Separates science from values/preferences
- Risk-of-bias assessment adapted for environmental studies

**Operationalization:** Relevant for Ehrlich's toxicology domain. When the research question is environmental/toxicological, use PECO instead of PICO and integrate evidence from multiple study types (in vivo, in vitro, computational).

**Citation:** Woodruff & Sutton (2014) Environ Health Perspect 122:1007-14. https://pubmed.ncbi.nlm.nih.gov/24968373/

### OHAT Framework (NTP)

7-step framework from the National Toxicology Program for literature-based health assessments:
1. Problem formulation and protocol
2. Search and select studies
3. Extract data
4. Assess risk of bias (6 domains, 4-point scale)
5. Rate confidence in body of evidence
6. Translate confidence into evidence levels
7. Integrate evidence streams (human + animal + mechanistic)

Risk-of-bias domains: participant selection, confounding, attrition/exclusion, detection, selective reporting, other.

**Operationalization:** Provides a structured pipeline that maps directly to agent workflow steps. Each step can be logged as a PRISMA-compatible record.

**Citation:** NTP OHAT Handbook (2015, revised 2019). https://ntp.niehs.nih.gov/sites/default/files/ntp/ohat/pubs/handbookjan2015_508.pdf

### ToxRTool (EU Toxicological Data Reliability)

Tool from the European Commission's Joint Research Centre for assessing reliability of toxicological data.

- Two templates: in vitro (18 criteria) and in vivo (21 criteria)
- Binary scoring (0 or 1/2 per criterion)
- Maps to Klimisch categories: 1 (reliable without restriction), 2 (reliable with restriction), 3 (not reliable)
- Increases transparency and harmonizes reliability assessment

**Operationalization:** When Ehrlich encounters toxicological data (e.g., EPA CompTox results), classify data reliability using Klimisch-like categories based on source metadata (peer-reviewed journal vs. database estimate vs. QSAR prediction).

**Citation:** Schneider et al. (2009) Toxicol Lett 189:138-44. https://pubmed.ncbi.nlm.nih.gov/19477248/

### Search Saturation

When to stop searching:
- When additional queries yield negligible new unique results
- Empirical guidance: search at least 2 major databases plus others (Greenhalgh & Peacock show 3+ strategies needed)
- Stopping rule: "no new inclusions in last N queries" or "<5% yield threshold"

**Operationalization:** Monitor pool of unique studies. Measure marginal gain per query round. Stop when additional searches add negligible unique results.

## 10 Universal Components

All frameworks converge on these requirements for a rigorous literature survey. Expanded from 8 to 10 after additional research (Greenhalgh & Peacock, GRADE, AMSTAR 2):

| # | Component | Description | Key Source |
|---|-----------|-------------|------------|
| 1 | **Clear Research Question** | PICO/PECO-structured question guides queries and eligibility. | Richardson (1995), Morgan (2018) |
| 2 | **Pre-specified Protocol** | Inclusion/exclusion rules, search strategy, quality criteria fixed BEFORE searching. | Cochrane, PRISMA, OHAT |
| 3 | **Multi-Strategy Search** | Database queries + snowballing + related-paper recommendations. Only 30% of sources come from database search alone. | Greenhalgh & Peacock (2005) |
| 4 | **Comprehensiveness** | Multiple databases (min 2). No single source suffices. Cross-check references. | Cochrane, PRISMA |
| 5 | **Transparent Documentation** | Every step logged: queries, filters, counts, exclusion reasons. PRISMA flow. | PRISMA, RAISE |
| 6 | **Evidence Quality Appraisal** | Each study rated by evidence level. Use domain-appropriate hierarchy (clinical: CEBM; molecular: measurement fidelity). | GRADE, CEBM, OECD QSAR |
| 7 | **Body-of-Evidence Rating** | Overall quality of the evidence body: high/moderate/low/very low. Not just individual studies. | GRADE (Guyatt, 2008) |
| 8 | **Bias Mitigation** | Publication bias (gray lit, preprints), selection bias (strict criteria), reporting bias (registry checks). | Egger (1997), Cochrane |
| 9 | **Saturation / Stopping Rule** | Stop when additional queries add <threshold unique results. Monitor marginal gain. | Cochrane, Greenhalgh |
| 10 | **Self-Assessment** | Review process evaluated against quality checklist (AMSTAR 2 critical domains). Report which standards met/unmet. | AMSTAR 2 (Shea, 2017) |

## Gap Research (Round 2)

### 1. Evidence Hierarchy for Molecular & Computational Science

No single universally accepted hierarchy exists, but several communities converge on an implicit gradient.

**Sources (all verified):**
- OECD QSAR Validation Principles (2004, revised 2014) -- 5 principles for computational predictions to count as credible evidence. https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/assessment-of-chemicals/oecd-principles-for-the-validation-for-regulatory-purposes-of-quantitative-structure-activity-relationship-models.pdf
- Trott & Olson (2010) -- docking as hypothesis generation, not proof
- Mobley & Gilson (2017) -- "Predicting binding free energies: Frontiers and benchmarks". RMS errors 1-2 kcal/mol with current force fields. https://pmc.ncbi.nlm.nih.gov/articles/PMC5544526/
- Ioannidis (2005) -- "Why Most Published Research Findings Are False" (PLoS Medicine). Landmark reproducibility paper.
- Begley & Ellis (2012) -- Only 6 of 53 preclinical studies reproduced. Nature 483:531-533. https://www.nature.com/articles/483531a
- SAMPL Challenges (Mobley et al., 2008-present) -- Community blind prediction benchmarks for free energy, pKa, logP. Prospective validation of computational methods. https://en.wikipedia.org/wiki/SAMPL_Challenge
- CASP (Moult et al., 1994-present) -- Critical Assessment of Structure Prediction. Biennial blind protein structure prediction benchmark. Validated AlphaFold. https://en.wikipedia.org/wiki/CASP

**Key insight from SAMPL/CASP:** Blind prediction challenges are the gold standard for establishing computational method credibility. A method validated via blind challenge ranks higher than one validated only retrospectively.

**Synthesized Evidence Hierarchy (Domain-Agnostic for Molecular Science):**

| Level | Evidence Type | Examples |
|-------|--------------|----------|
| 1 | Direct experimental measurement | Crystal structure, IC50 assay, binding calorimetry, SPR |
| 2 | Independent replication | Same measurement reproduced by another lab |
| 3 | Orthogonal experimental support | Structure + assay; assay + phenotypic effect |
| 4 | Physics-based simulation | FEP, MD with validated force fields |
| 5 | Empirical/statistical model | QSAR, ML predictions with validation |
| 6 | Heuristic / unvalidated model | Docking score alone, rule-of-thumb |

**OECD QSAR Validation Principles (5 requirements for computational evidence):**
1. Defined endpoint
2. Unambiguous algorithm
3. Defined applicability domain
4. Appropriate measures of goodness-of-fit, robustness, predictivity
5. Mechanistic interpretation (if possible)

A computational result violating any principle is lower evidence than one satisfying all.

**Operationalization:**
- Parse methods section keywords to classify evidence level:
  - "X-ray crystallography", "ITC", "SPR" -> Level 1
  - "molecular dynamics", "free energy perturbation" -> Level 4
  - "QSAR", "random forest", "deep learning" -> Level 5
- Evidence scoring: `BaseLevel + ReplicationBonus + OrthogonalSupportBonus - ApplicabilityDomainPenalty`

**Key insight:** Evidence strength = measurement fidelity + reproducibility + validation. RCTs are just one instantiation for clinical science.

---

### 2. Scoping Reviews vs. Systematic Reviews

**Sources:**
- Arksey & O'Malley (2005) -- Scoping studies: towards a methodological framework
- Levac et al. (2010) -- refinement of Arksey & O'Malley
- Tricco et al. (2018) -- PRISMA-ScR extension for scoping reviews

**Key differences:**

| Dimension | Systematic Review | Scoping Review |
|-----------|------------------|----------------|
| Goal | Answer a precise question | Map the landscape |
| Question | Narrow, specific | Broad, exploratory |
| Quality appraisal | Required | Optional |
| Synthesis | Comparative, often quantitative | Descriptive, thematic |
| Bias control | Central | Secondary |
| Endpoint | Best answer | What exists? |

**When scoping is more appropriate:**
- Field is immature or fragmented
- Concepts and definitions not standardized
- Goal is hypothesis generation, not testing

This exactly matches AI-driven molecular exploration. Ehrlich's literature survey is a scoping review.

**Operationalization:**
- No exclusion by evidence quality (broad inclusion)
- Wider query expansion than systematic
- Cluster papers by technique, molecular class, endpoint
- **Transition logic:** When concept clusters stabilize -> switch to systematic mode for focused hypothesis testing

---

### 3. Rapid Review Methodology

**Sources:**
- Tricco et al. (2015) -- rapid review methods
- Cochrane Rapid Reviews Methods Group (2020)
- WHO Rapid Evidence Synthesis (2017)

**Acceptable shortcuts in rapid reviews:**

| Shortcut | Accepted? |
|----------|-----------|
| Fewer databases | Yes |
| Language restrictions | Yes |
| Single screener | Yes |
| Automated screening | Yes |
| Narrative synthesis | Yes |
| No meta-analysis | Yes |

**NOT acceptable (even in rapid reviews):**
- Undefined eligibility criteria
- Undocumented decisions

**Core principle:** Rapid != sloppy, just bounded. Trade recall for speed, preserve transparency.

**Operationalization:**
- Limit to 2 databases (PubMed + Semantic Scholar)
- Cap snowball depth (1-2 levels)
- Time-budgeted search loop
- Explicit confidence downgrade flag: `review_type: "rapid", confidence: "moderate"`

---

### 4. Automated Screening (ML-Assisted)

**Sources:**
- Wallace et al. (2010) -- ML for screening
- Cohen et al. (2011) -- Abstrackr
- Miwa et al. (2014) -- text mining for reviews
- Bannach-Brown et al. (2019) -- automation performance
- Marshall & Wallace (2019) -- systematic review automation
- ASReview (van de Schoot et al., 2021) -- open-source active learning, published in Nature Machine Intelligence. Reduces up to 95% screening time. https://www.nature.com/articles/s42256-020-00287-7
- RAISE (Cochrane/Campbell/JBI, 2025) -- Responsible AI in Evidence Synthesis. Joint position statement: AI must have human oversight, be disclosed, and authors remain accountable. https://osf.io/fwaud/

**Validated performance:** Studies show 95% recall achievable after screening ~34-40% of total references (not 95-99% as sometimes overstated). Most errors are false positives, not false negatives. Active ML saves 62-71% of screening work at 95% recall threshold. ASReview v2 improves performance by 24.1% over v1 using SYNERGY benchmark.

**Key principle:** Optimize for RECALL, not precision. Missing a relevant paper is worse than including an irrelevant one.

**RAISE requirements for AI-assisted screening:**
- AI use must be disclosed and transparent
- Human oversight required (human-in-the-loop)
- Authors accountable for final content
- Must justify why AI is used and demonstrate it doesn't compromise rigor
- Report AI methods in manuscript

**Best practices:**
1. Conservative inclusion thresholds
2. Active learning (update model as papers included) -- see ASReview
3. Dual-pass logic (model + keyword rules)
4. Human override optional for AI agents, but RAISE requires disclosure
5. LLMs (GPT-4, Claude, Gemini) achieve >85% accuracy on PICO extraction from abstracts

**Operationalization:**
- Hybrid inclusion: `Include if ML_relevance > threshold OR keyword_match_strong`
- Train on prior accepted papers as positives (titles + abstracts)
- Each exclusion carries uncertainty score
- High-uncertainty exclusions can be re-queried in later rounds
- Log all AI-assisted decisions per RAISE transparency requirements

---

### 5. PICO Adaptation for Molecular Science

**Published alternatives (verified):**
- **PECO** (Population, Exposure, Comparator, Outcome) -- Morgan et al. (2018), Environment International. Used by EPA/NTP for toxicology and environmental health. https://pubmed.ncbi.nlm.nih.gov/30166065/
- **SPIDER** (Sample, Phenomenon, Design, Evaluation, Research type) -- Cooke et al. (2012). Designed for qualitative research.

**Not verified (ChatGPT fabrication):**
- ~~"Gupta et al. (2021) Target-Perturbation-Readout"~~ -- No such named framework exists. The Gupta 2021 paper is a general ML/drug discovery review, not a PICO alternative.

**Recommended mapping for Ehrlich (domain-agnostic):**

| Element | PICO Clinical | Molecular Science Equivalent |
|---------|--------------|------------------------------|
| P (Population) | Patient group | Target: protein, pathway, organism, disease |
| I (Intervention) | Treatment | Modality: small molecule, compound class, modification |
| C (Comparison) | Control/placebo | Reference: known actives, known inactives, controls |
| O (Outcome) | Clinical endpoint | Readout: binding affinity, activity (IC50/MIC/Ki), toxicity, ADMET |

Additional dimensions for computational science:
- **E (Evidence type):** experimental vs computational (maps to evidence hierarchy)
- **G (Ground truth):** what validates the result (crystal structure, assay, benchmark)

**Operationalization:**
- Each search decomposed into PICO-M dimensions (P, I, C, O + Modality)
- Each dimension becomes a query axis with Boolean expansion
- Evidence type constrains confidence scoring
- Scoping mode: loose PICO-M matching; Systematic mode: strict matching

## Ehrlich's Review Mode

Based on the research above, Ehrlich operates as a **rapid scoping review**:
- Broad exploratory search (scoping)
- Time-constrained (rapid)
- Automated screening (ML-assisted relevance)
- Transparent documentation (PRISMA-lite logging)
- Transitions to focused systematic queries once landscape is mapped

This is a recognized and defensible methodology, not a shortcut.

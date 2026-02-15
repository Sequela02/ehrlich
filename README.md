# Ehrlich

Open-source (AGPL-3.0), self-hostable scientific discovery engine. Ehrlich uses Claude as a hypothesis-driven scientific reasoning engine that works across multiple scientific domains. The core engine is domain-agnostic: a pluggable `DomainConfig` system lets any domain bring its own tools, scoring, and visualization. Run it on your own infrastructure with your own API keys, or use the [hosted instance](https://app.ehrlich.dev) where credits cover the Anthropic API costs.

Named after Paul Ehrlich, the father of the "magic bullet" -- finding the right answer for any question.

Built for the [Claude Code Hackathon](https://docs.anthropic.com/en/docs/claude-code-hackathon) (Feb 10-16, 2026).

## Philosophy

Ehrlich is **COSS** (Commercial Open-Source Software) -- the same model used by Supabase, PostHog, Cal.com, and GitLab. The entire codebase is open source under AGPL-3.0. There is no proprietary version.

**Two paths, same product:**

| Path | How It Works | Cost |
|------|-------------|------|
| **Self-host** | Clone the repo, bring your own Anthropic API key | Free. No limits, no credits, no account needed |
| **Hosted instance** | Use app.ehrlich.dev | Credits cover Anthropic API costs (Opus is expensive) |

Credits exist because Claude Opus costs real money per investigation. They make scientific reasoning **accessible** -- not monetized. A student in Mexico and a pharma company in Boston get the same 90 tools, the same 24 data sources, the same methodology. The model quality is the only variable.

The AI is the scientist. The platform is the laboratory.

## What Can Ehrlich Investigate?

Ehrlich is **domain-agnostic**. The hypothesis-driven engine works for any scientific domain:

### Molecular Science
- **Antimicrobial resistance** -- "Find novel compounds active against MRSA"
- **Drug discovery** -- "What compounds in Lycopodium selago could treat Alzheimer's?"
- **Environmental toxicology** -- "Which microplastic degradation products are most toxic?"
- **Agricultural biocontrol** -- "Find biocontrol molecules from endophytic bacteria in Mammillaria"
- **Any molecular target** -- dynamic protein target discovery from 200K+ PDB structures

### Training Science
- **Training optimization** -- "What are the most effective protocols for improving VO2max?"
- **Injury prevention** -- "Evaluate ACL injury prevention programs for female soccer players"

### Nutrition Science
- **Supplement evidence** -- "What is the evidence for creatine on strength performance?"
- **Nutrient profiling** -- "Compare protein content and amino acid profiles of whey vs plant-based supplements"

### Impact Evaluation
- **Social program analysis** -- "Evaluate the effectiveness of Sonora's sports scholarship program"
- **Causal inference** -- "Does the conditional cash transfer reduce school dropout rates?" (4 methods: DiD, PSM, RDD, Synthetic Control)
- **Cross-country benchmarking** -- "Compare cost-effectiveness of state sports programs in Mexico"
- Economic indicators from World Bank, WHO GHO, FRED, Census Bureau, and BLS
- US federal data: USAspending grants, College Scorecard education outcomes, HUD housing data, CDC WONDER mortality/natality, data.gov open datasets
- Cross-program comparison and international benchmarking
- Domain-agnostic causal inference tools (in analysis/ context) usable by any domain

## Architecture

Ehrlich follows Domain-Driven Design with eleven bounded contexts:

| Context | Purpose |
|---------|---------|
| **kernel** | Shared primitives: SMILES, Molecule, exceptions |
| **shared** | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D) |
| **literature** | Scientific paper search (Semantic Scholar) and reference management |
| **chemistry** | Cheminformatics: molecular descriptors, fingerprints, 3D conformers |
| **analysis** | Dataset exploration (ChEMBL, PubChem), substructure enrichment, domain-agnostic causal inference (DiD, PSM, RDD, Synthetic Control) |
| **prediction** | ML modeling: train, predict, ensemble, cluster |
| **simulation** | Molecular docking, ADMET, resistance, target discovery (RCSB PDB), toxicity (EPA CompTox) |
| **training** | Exercise physiology: evidence analysis, protocol comparison, injury risk, training metrics, clinical trials |
| **nutrition** | Nutrition science: supplement evidence, labels, nutrients, safety, interactions, adequacy, inflammatory index |
| **investigation** | Multi-model agent orchestration with Director-Worker-Summarizer pattern + domain registry + MCP bridge |
| **impact** | Social program evaluation: economic indicators (World Bank, WHO GHO, FRED, Census, BLS), health (CDC WONDER), spending (USAspending), education (College Scorecard), housing (HUD), open data (data.gov). Causal estimators live in analysis/ (domain-agnostic) |

### Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence, synthesizes (3-5 calls)
Sonnet 4.5 (Researcher) -- Executes experiments with 90 tools (10-20 calls)
Haiku 4.5 (Summarizer)  -- Compresses large outputs, classifies domains (5-10 calls)
```

Cost: ~$3-4 per investigation (vs ~$11 with all-Opus).

### Data Sources

| Source | What It Provides | Coverage |
|--------|-----------------|----------|
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Bioactivity data (MIC, IC50, Ki, EC50, Kd) | 2.5M+ compounds, 15K+ targets |
| [RCSB PDB](https://www.rcsb.org/) | Protein target discovery by organism/function | 200K+ structures |
| [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Compound search by target/activity/similarity | 100M+ compounds |
| [EPA CompTox](https://www.epa.gov/comptox-tools) | Environmental toxicity, bioaccumulation, fate | 1M+ chemicals |
| [Semantic Scholar](https://www.semanticscholar.org/) | Scientific literature search | 200M+ papers |
| [UniProt](https://www.uniprot.org/) | Protein function, disease associations, GO terms | 250M+ sequences |
| [Open Targets](https://platform.opentargets.org/) | Disease-target associations (scored evidence) | 60K+ targets |
| [GtoPdb](https://www.guidetopharmacology.org/) | Expert-curated pharmacology (pKi, pIC50) | 11K+ ligands |
| [ClinicalTrials.gov](https://clinicaltrials.gov/) | Registered exercise/training RCTs | 500K+ studies |
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | Biomedical literature with MeSH terms | 37M+ articles |
| [wger](https://wger.de/) | Exercise database (muscles, equipment, categories) | 300+ exercises |
| [NIH DSLD](https://dsld.od.nih.gov/) | Dietary supplement label database | 120K+ products |
| [USDA FoodData](https://fdc.nal.usda.gov/) | Nutrient profiles for foods and supplements | 1.1M+ foods |
| [OpenFDA CAERS](https://open.fda.gov/) | Supplement adverse event reports | 200K+ reports |
| [RxNav](https://rxnav.nlm.nih.gov/) | Drug interaction screening (RxCUI resolution) | 100K+ drugs |
| [World Bank](https://data.worldbank.org/) | Development indicators by country (GDP, poverty, education) | 190+ countries |
| [WHO GHO](https://www.who.int/data/gho) | Global health statistics (life expectancy, mortality, disease) | 190+ countries |
| [FRED](https://fred.stlouisfed.org/) | US economic time series (GDP, unemployment, CPI) | 800K+ series |
| [Census Bureau](https://data.census.gov/) | US demographics, poverty, education (ACS 5-year) | 50 states + territories |
| [BLS](https://www.bls.gov/) | US labor statistics (unemployment, CPI, wages) | 130K+ series |
| [USAspending](https://www.usaspending.gov/) | Federal spending awards and grants | All federal agencies |
| [College Scorecard](https://collegescorecard.ed.gov/) | US higher education outcomes (completion, earnings) | 6K+ institutions |
| [HUD](https://www.huduser.gov/) | Fair Market Rents, income limits, housing data | All US counties |
| [CDC WONDER](https://wonder.cdc.gov/) | US mortality, natality, public health statistics | National-level |

All data sources are free and open-access.

## 90 Tools

| Context | Tool | Description |
|---------|------|-------------|
| Chemistry | `validate_smiles` | Validate SMILES string |
| Chemistry | `compute_descriptors` | MW, LogP, TPSA, HBD, HBA, QED, rings |
| Chemistry | `compute_fingerprint` | Morgan (2048-bit) or MACCS (166-bit) |
| Chemistry | `tanimoto_similarity` | Similarity between two molecules (0-1) |
| Chemistry | `generate_3d` | 3D conformer with MMFF94 optimization |
| Chemistry | `substructure_match` | SMARTS/SMILES substructure search |
| Literature | `search_literature` | Semantic Scholar paper search |
| Literature | `search_citations` | Citation chasing (snowballing) via references/citing |
| Literature | `get_reference` | Curated reference lookup |
| Analysis | `explore_dataset` | Load ChEMBL bioactivity data for any target |
| Analysis | `search_bioactivity` | Flexible ChEMBL query (any assay type) |
| Analysis | `search_compounds` | PubChem compound search |
| Analysis | `analyze_substructures` | Chi-squared enrichment analysis |
| Analysis | `compute_properties` | Property distributions (active vs inactive) |
| Analysis | `search_pharmacology` | GtoPdb curated receptor/ligand interactions |
| Causal | `estimate_did` | Difference-in-differences causal estimation |
| Causal | `estimate_psm` | Propensity score matching with balance diagnostics |
| Causal | `estimate_rdd` | Regression discontinuity design (sharp/fuzzy) |
| Causal | `estimate_synthetic_control` | Synthetic control method |
| Causal | `assess_threats` | Validity threat assessment for causal methods |
| Causal | `compute_cost_effectiveness` | Cost per unit outcome, ICER |
| Prediction | `train_model` | Train XGBoost on SMILES+activity data |
| Prediction | `predict_candidates` | Score compounds with trained model |
| Prediction | `cluster_compounds` | Butina structural clustering |
| ML | `train_classifier` | Train binary classifier on tabular feature data (any domain) |
| ML | `predict_scores` | Score samples with trained classifier (any domain) |
| ML | `cluster_data` | Hierarchical clustering on tabular features (any domain) |
| Simulation | `search_protein_targets` | RCSB PDB target discovery by organism/function |
| Simulation | `dock_against_target` | Descriptor-based binding energy estimation |
| Simulation | `predict_admet` | Drug-likeness profiling |
| Simulation | `fetch_toxicity_profile` | EPA CompTox environmental toxicity |
| Simulation | `assess_resistance` | Resistance mutation scoring |
| Simulation | `get_protein_annotation` | UniProt protein function and disease links |
| Simulation | `search_disease_targets` | Open Targets disease-target associations |
| Training | `search_training_literature` | Training science literature with MeSH expansion, study type ranking, non-human filtering |
| Training | `analyze_training_evidence` | Pooled effect sizes, heterogeneity, evidence grading |
| Training | `compare_protocols` | Evidence-weighted protocol comparison |
| Training | `assess_injury_risk` | Knowledge-based injury risk scoring |
| Training | `compute_training_metrics` | ACWR, monotony, strain, session RPE load |
| Training | `search_clinical_trials` | ClinicalTrials.gov exercise/training RCT search |
| Training | `search_pubmed_training` | PubMed literature search with MeSH terms |
| Training | `search_exercise_database` | Exercise database by muscle/equipment/category |
| Training | `compute_performance_model` | Banister fitness-fatigue model (CTL/ATL/TSB) |
| Training | `compute_dose_response` | Dose-response curve from dose-effect data |
| Training | `plan_periodization` | Evidence-based periodization planning (linear/undulating/block) |
| Nutrition | `search_supplement_evidence` | Supplement evidence with GRADE-style ranking, retracted paper exclusion |
| Nutrition | `search_supplement_labels` | NIH DSLD supplement product ingredient lookup |
| Nutrition | `search_nutrient_data` | USDA FoodData Central nutrient profiles |
| Nutrition | `search_supplement_safety` | OpenFDA CAERS adverse event reports |
| Nutrition | `compare_nutrients` | Side-by-side nutrient comparison with per-nutrient deltas, winner, MAR score |
| Nutrition | `assess_nutrient_adequacy` | DRI-based nutrient adequacy assessment |
| Nutrition | `check_intake_safety` | Tolerable Upper Intake Level safety screening |
| Nutrition | `check_interactions` | Drug-supplement interaction screening via RxNav |
| Nutrition | `analyze_nutrient_ratios` | Key nutrient ratio analysis (omega-6:3, Ca:Mg, etc.) |
| Nutrition | `compute_inflammatory_index` | Simplified Dietary Inflammatory Index scoring |
| Impact | `search_economic_indicators` | Query economic time series from FRED, BLS, Census, World Bank, or WHO GHO |
| Impact | `search_health_indicators` | Search WHO GHO or CDC WONDER for health indicators |
| Impact | `fetch_benchmark` | Get comparison values from international or US data sources |
| Impact | `compare_programs` | Cross-program comparison using statistical tests |
| Impact | `search_spending_data` | Search USAspending.gov for federal spending awards and grants |
| Impact | `search_education_data` | Search College Scorecard for US higher education outcomes |
| Impact | `search_housing_data` | Search HUD for Fair Market Rents and income limits |
| Impact | `search_open_data` | Search data.gov CKAN catalog for US federal open datasets |
| Visualization | `render_binding_scatter` | Scatter plot of compound binding affinities |
| Visualization | `render_admet_radar` | Radar chart of ADMET/drug-likeness properties |
| Visualization | `render_training_timeline` | Training load timeline with ACWR danger zones |
| Visualization | `render_muscle_heatmap` | Anatomical body diagram with muscle activation |
| Visualization | `render_forest_plot` | Forest plot for meta-analysis results |
| Visualization | `render_evidence_matrix` | Hypothesis-by-evidence support/contradiction heatmap |
| Visualization | `render_performance_chart` | Banister fitness-fatigue performance chart |
| Visualization | `render_funnel_plot` | Funnel plot for publication bias assessment |
| Visualization | `render_dose_response` | Dose-response curve with confidence intervals |
| Visualization | `render_nutrient_comparison` | Grouped bar chart comparing nutrient profiles |
| Visualization | `render_nutrient_adequacy` | Horizontal bar chart with DRI adequacy + MAR score |
| Visualization | `render_therapeutic_window` | Therapeutic window chart (EAR/RDA/AI/UL zones) |
| Visualization | `render_program_dashboard` | Multi-indicator KPI dashboard with target tracking |
| Visualization | `render_geographic_comparison` | Region bar chart with benchmark reference line |
| Visualization | `render_parallel_trends` | DiD parallel trends chart (treatment vs control) |
| Visualization | `render_rdd_plot` | Regression discontinuity scatter with cutoff line |
| Visualization | `render_causal_diagram` | DAG showing treatment, outcome, confounders |
| Statistics | `run_statistical_test` | Compare two numeric groups (auto-selects t-test/Welch/Mann-Whitney) |
| Statistics | `run_categorical_test` | Test contingency tables (auto-selects Fisher's exact/chi-squared) |
| Investigation | `propose_hypothesis` | Register testable hypothesis |
| Investigation | `design_experiment` | Plan experiment with tool sequence |
| Investigation | `evaluate_hypothesis` | Assess outcome with confidence score |
| Investigation | `record_finding` | Record finding linked to hypothesis |
| Investigation | `record_negative_control` | Validate model with known-inactive compounds |
| Investigation | `search_prior_research` | Search past investigation findings via full-text search |
| Investigation | `query_uploaded_data` | Query user-uploaded files (CSV/Excel filtering, PDF text) |
| Investigation | `conclude_investigation` | Final summary with ranked candidates |

## Tech Stack

- **Server:** Python 3.12, FastAPI, uv, PostgreSQL (asyncpg), httpx
- **Console:** React 19, TypeScript 5.6+, Bun, Vite 7+, TanStack Router, 3Dmol.js, WorkOS AuthKit
- **AI:** Claude Opus 4.6 + Sonnet 4.5 + Haiku 4.5 (Anthropic API) with tool use
- **Science:** RDKit, Chemprop, XGBoost, PyArrow
- **Visualization:** 3Dmol.js (live 3D molecular scene), React Flow (investigation diagrams)
- **Data:** ChEMBL, RCSB PDB, PubChem, EPA CompTox, Semantic Scholar (all free APIs)

## Quick Start

> **Self-hosting?** You use your own Anthropic API key directly -- no credits, no account, no hosted dependency. The credit system only applies to the managed hosted instance.

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (JavaScript runtime)
- Python 3.12
- PostgreSQL 16+
- An Anthropic API key

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EHRLICH_ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `ANTHROPIC_API_KEY` | Alt | Falls back to this if EHRLICH_ not set |
| `EHRLICH_DATABASE_URL` | Yes | PostgreSQL connection URL (default: `postgresql://postgres:postgres@localhost:5432/ehrlich`) |
| `EHRLICH_WORKOS_CLIENT_ID` | Yes | WorkOS AuthKit client ID (authentication) |
| `EHRLICH_WORKOS_API_KEY` | Yes | WorkOS API key (authentication) |
| `EHRLICH_DIRECTOR_MODEL` | No | Director model (default: `claude-opus-4-6`) |
| `EHRLICH_RESEARCHER_MODEL` | No | Researcher model (default: `claude-sonnet-4-5-20250929`) |
| `EHRLICH_SUMMARIZER_MODEL` | No | Summarizer model (default: `claude-haiku-4-5-20251001`) |
| `EHRLICH_SUMMARIZER_THRESHOLD` | No | Chars before Haiku summarizes output (default: 2000) |
| `EHRLICH_ANTHROPIC_MODEL` | No | Single-model fallback (overrides all three) |
| `EHRLICH_MAX_ITERATIONS` | No | Max agent loop iterations (default: 50) |
| `EHRLICH_MAX_ITERATIONS_PER_PHASE` | No | Max iterations per experiment in multi-model mode (default: 10) |
| `EHRLICH_LOG_LEVEL` | No | Logging level (default: INFO) |
| `EHRLICH_COMPTOX_API_KEY` | No | EPA CompTox API key (free, for toxicity data) |

### Database

```bash
# Create the PostgreSQL database
createdb ehrlich
# Or via psql:
# psql -c "CREATE DATABASE ehrlich;"
```

### Server

```bash
cd server
uv sync --extra dev                    # Core + dev dependencies
# uv sync --extra all --extra dev      # All deps including deep learning
export EHRLICH_ANTHROPIC_API_KEY=sk-ant-...
export EHRLICH_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ehrlich
export EHRLICH_WORKOS_CLIENT_ID=client_...
export EHRLICH_WORKOS_API_KEY=sk_...
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
```

Optional dependency groups:
- `deeplearning` -- Chemprop D-MPNN (pulls PyTorch)
- `all` -- everything

### Console

```bash
cd console
bun install
bun dev
```

Open http://localhost:5173 in your browser.

### Data Preparation (Optional)

Pre-download ChEMBL bioactivity data to avoid first-run delays:

```bash
# Download bioactivity data for all target organisms
uv run python data/scripts/prepare_data.py --chembl

# Download protein structures from RCSB PDB
uv run python data/scripts/prepare_data.py --proteins

# Download everything
uv run python data/scripts/prepare_data.py --all
```

Cached datasets are stored in `data/datasets/` as parquet files.

### Docker

```bash
docker compose up
```

Server at :8000, Console at :3000.

## API Endpoints

### Public (no auth required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/methodology` | Methodology: phases, domains, tools, data sources, models |
| GET | `/api/v1/stats` | Aggregate counts (tools, domains, phases, data sources, events) |
| GET | `/api/v1/molecule/depict?smiles=&w=&h=` | 2D SVG depiction (`image/svg+xml`, cached 24h) |
| GET | `/api/v1/molecule/conformer?smiles=` | 3D conformer (JSON: mol_block, energy, num_atoms) |
| GET | `/api/v1/molecule/descriptors?smiles=` | Molecular descriptors + Lipinski pass/fail |
| GET | `/api/v1/targets` | List protein targets (pdb_id, name, organism) |

### Protected (WorkOS JWT required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/investigate` | List user's investigations (most recent first) |
| POST | `/api/v1/investigate` | Create new investigation (`director_tier`: haiku/sonnet/opus) |
| GET | `/api/v1/investigate/{id}` | Full investigation detail (owner only) |
| GET | `/api/v1/investigate/{id}/stream` | SSE stream of investigation events (owner only, supports `?token=`) |
| GET | `/api/v1/investigate/{id}/paper` | Structured scientific paper + visualizations from completed investigation (owner only). PDF via `/paper/:id` route + browser print |
| POST | `/api/v1/investigate/{id}/approve` | Approve/reject formulated hypotheses (owner only) |
| POST | `/api/v1/upload` | Upload file (CSV/XLSX/PDF) for investigation data, returns preview |
| GET | `/api/v1/credits/balance` | Current credit balance + BYOK status |

### SSE Event Types

| Event | Description |
|-------|-------------|
| `hypothesis_formulated` | Hypothesis with prediction, criteria, scope, prior confidence |
| `experiment_started` | Experiment execution begins |
| `experiment_completed` | Experiment finished with results |
| `hypothesis_evaluated` | Outcome assessed against pre-defined criteria |
| `negative_control` | Model validation result (known-inactive compound) |
| `positive_control` | Model validation result (known-active compound) |
| `validation_metrics` | Z'-factor, control separation stats |
| `tool_called` | Tool invocation with inputs |
| `tool_result` | Tool output preview |
| `finding_recorded` | Scientific finding with evidence level |
| `thinking` | Model reasoning text |
| `output_summarized` | Haiku compressed a large output |
| `literature_survey_completed` | PICO, search stats, evidence grade |
| `phase_changed` | Investigation phase transition (1-6) |
| `cost_update` | Progressive cost/token snapshot |
| `hypothesis_approval_requested` | Awaiting user approval of hypotheses |
| `domain_detected` | Domain identified with display config |
| `visualization` | Chart/diagram visualization rendered |
| `completed` | Investigation finished with candidates and cost |
| `error` | Error occurred |

## Demo

1. Start the server: `cd server && uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`
2. Start the console: `cd console && bun dev`
3. Open http://localhost:5173
4. Type any research question or pick a template, for example:
   - *"Find novel antimicrobial candidates against MRSA"*
   - *"What compounds in Lycopodium selago could treat Alzheimer's?"*
   - *"Which microplastic degradation products are most toxic?"*
   - *"What are the most effective training protocols for improving VO2max?"*
   - *"Evaluate ACL injury prevention programs for female soccer players"*
5. Watch the investigation unfold in real-time via SSE streaming
6. See domain-specific visualizations: molecular investigations show a 3D Live Lab (proteins load, ligands dock, candidates glow by score); training investigations show timeline charts and body diagrams; all domains render forest plots and evidence matrices
7. View ranked candidates with domain-specific score columns in the results table
8. Click any candidate row to expand the detail panel with domain-specific views (molecular: 3D conformer, properties, Lipinski; training/nutrition: scores, attributes)
9. Browse the hypothesis board showing formulated, tested, supported, and refuted hypotheses
10. Explore the auto-generated investigation diagram: SVG hypothesis map with status-colored nodes and evidence-chain arrows
11. After completion, view the structured investigation report: research question, executive summary, hypotheses, methodology, findings, candidates, model validation, and cost breakdown
12. Reload a completed investigation and see the full timeline replayed from stored events
13. View past investigations in the history section on the home page

## Development

### Server Commands

```bash
uv run pytest --cov=ehrlich --cov-report=term-missing   # Tests + coverage
uv run ruff check src/ tests/                            # Lint
uv run ruff format src/ tests/                           # Format
uv run mypy src/ehrlich/                                 # Type check
```

### Console Commands

```bash
bunx vitest run   # Vitest
bun run build     # vite build (generates routes + bundles)
bun run typecheck # tsc --noEmit (run after build to ensure route types exist)
```

### Quality Gates

| Gate | Tool | Threshold |
|------|------|-----------|
| Linting | ruff | Zero violations |
| Formatting | ruff format | Zero violations |
| Type checking | mypy (strict) | Zero errors |
| Test coverage | pytest-cov | 80% minimum |
| TypeScript | tsc --noEmit | Zero errors |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, architecture overview, and code conventions.

## License

AGPL-3.0 - see [LICENSE](LICENSE).

## Author

Ricardo Armenta / [Sequel](https://github.com/Sequela02)

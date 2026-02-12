# Ehrlich

AI-powered scientific discovery engine. Ehrlich uses Claude as a hypothesis-driven scientific reasoning engine that works across multiple scientific domains. The core engine is domain-agnostic: a pluggable `DomainConfig` system lets any domain bring its own tools, scoring, and visualization.

Named after Paul Ehrlich, the father of the "magic bullet" -- finding the right answer for any question.

Built for the [Claude Code Hackathon](https://docs.anthropic.com/en/docs/claude-code-hackathon) (Feb 10-16, 2026).

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

## Architecture

Ehrlich follows Domain-Driven Design with ten bounded contexts:

| Context | Purpose |
|---------|---------|
| **kernel** | Shared primitives: SMILES, Molecule, exceptions |
| **shared** | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D) |
| **literature** | Scientific paper search (Semantic Scholar) and reference management |
| **chemistry** | Cheminformatics: molecular descriptors, fingerprints, 3D conformers |
| **analysis** | Dataset exploration (ChEMBL, PubChem), substructure enrichment |
| **prediction** | ML modeling: train, predict, ensemble, cluster |
| **simulation** | Molecular docking, ADMET, resistance, target discovery (RCSB PDB), toxicity (EPA CompTox) |
| **training** | Exercise physiology: evidence analysis, protocol comparison, injury risk, training metrics, clinical trials |
| **nutrition** | Nutrition science: supplement evidence, supplement labels, nutrient data, supplement safety |
| **investigation** | Multi-model agent orchestration with Director-Worker-Summarizer pattern + domain registry + MCP bridge |

### Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence, synthesizes (3-5 calls)
Sonnet 4.5 (Researcher) -- Executes experiments with 48 tools (10-20 calls)
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
| [NIH DSLD](https://dsld.od.nih.gov/) | Dietary supplement label database | 120K+ products |
| [USDA FoodData](https://fdc.nal.usda.gov/) | Nutrient profiles for foods and supplements | 1.1M+ foods |
| [OpenFDA CAERS](https://open.fda.gov/) | Supplement adverse event reports | 200K+ reports |

All data sources are free and open-access.

## 48 Tools

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
| Prediction | `train_model` | Train XGBoost/Chemprop on any SMILES+activity data |
| Prediction | `predict_candidates` | Score compounds with trained model |
| Prediction | `cluster_compounds` | Butina structural clustering |
| Simulation | `search_protein_targets` | RCSB PDB target discovery by organism/function |
| Simulation | `dock_against_target` | AutoDock Vina docking (or RDKit fallback) |
| Simulation | `predict_admet` | Drug-likeness profiling |
| Simulation | `fetch_toxicity_profile` | EPA CompTox environmental toxicity |
| Simulation | `assess_resistance` | Resistance mutation scoring |
| Simulation | `get_protein_annotation` | UniProt protein function and disease links |
| Simulation | `search_disease_targets` | Open Targets disease-target associations |
| Training | `search_training_literature` | Training science literature via Semantic Scholar |
| Training | `analyze_training_evidence` | Pooled effect sizes, heterogeneity, evidence grading |
| Training | `compare_protocols` | Evidence-weighted protocol comparison |
| Training | `assess_injury_risk` | Knowledge-based injury risk scoring |
| Training | `compute_training_metrics` | ACWR, monotony, strain, session RPE load |
| Training | `search_clinical_trials` | ClinicalTrials.gov exercise/training RCT search |
| Nutrition | `search_supplement_evidence` | Supplement efficacy literature search |
| Nutrition | `search_supplement_labels` | NIH DSLD supplement product ingredient lookup |
| Nutrition | `search_nutrient_data` | USDA FoodData Central nutrient profiles |
| Nutrition | `search_supplement_safety` | OpenFDA CAERS adverse event reports |
| Visualization | `render_binding_scatter` | Scatter plot of compound binding affinities |
| Visualization | `render_admet_radar` | Radar chart of ADMET/drug-likeness properties |
| Visualization | `render_training_timeline` | Training load timeline with ACWR danger zones |
| Visualization | `render_muscle_heatmap` | Anatomical body diagram with muscle activation |
| Visualization | `render_forest_plot` | Forest plot for meta-analysis results |
| Visualization | `render_evidence_matrix` | Hypothesis-by-evidence support/contradiction heatmap |
| Investigation | `propose_hypothesis` | Register testable hypothesis |
| Investigation | `design_experiment` | Plan experiment with tool sequence |
| Investigation | `evaluate_hypothesis` | Assess outcome with confidence score |
| Investigation | `record_finding` | Record finding linked to hypothesis |
| Investigation | `record_negative_control` | Validate model with known-inactive compounds |
| Investigation | `search_prior_research` | Search past investigation findings via FTS5 |
| Investigation | `conclude_investigation` | Final summary with ranked candidates |

## Tech Stack

- **Server:** Python 3.12, FastAPI, uv, SQLite (aiosqlite), httpx
- **Console:** React 19, TypeScript 5.6+, Bun, Vite 7+, TanStack Router, 3Dmol.js
- **AI:** Claude Opus 4.6 + Sonnet 4.5 + Haiku 4.5 (Anthropic API) with tool use
- **Science:** RDKit, Chemprop, XGBoost, AutoDock Vina, Meeko, PyArrow
- **Visualization:** 3Dmol.js (live 3D molecular scene), React Flow (investigation diagrams)
- **Data:** ChEMBL, RCSB PDB, PubChem, EPA CompTox, Semantic Scholar (all free APIs)

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (JavaScript runtime)
- Python 3.12
- An Anthropic API key

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EHRLICH_ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `ANTHROPIC_API_KEY` | Alt | Falls back to this if EHRLICH_ not set |
| `EHRLICH_DIRECTOR_MODEL` | No | Director model (default: `claude-opus-4-6`) |
| `EHRLICH_RESEARCHER_MODEL` | No | Researcher model (default: `claude-sonnet-4-5-20250929`) |
| `EHRLICH_SUMMARIZER_MODEL` | No | Summarizer model (default: `claude-haiku-4-5-20251001`) |
| `EHRLICH_SUMMARIZER_THRESHOLD` | No | Chars before Haiku summarizes output (default: 2000) |
| `EHRLICH_ANTHROPIC_MODEL` | No | Single-model fallback (overrides all three) |
| `EHRLICH_MAX_ITERATIONS` | No | Max agent loop iterations (default: 50) |
| `EHRLICH_MAX_ITERATIONS_PER_PHASE` | No | Max iterations per experiment in multi-model mode (default: 10) |
| `EHRLICH_DB_PATH` | No | SQLite database path (default: `data/ehrlich.db`) |
| `EHRLICH_LOG_LEVEL` | No | Logging level (default: INFO) |
| `EHRLICH_COMPTOX_API_KEY` | No | EPA CompTox API key (free, for toxicity data) |

### Server

```bash
cd server
uv sync --extra dev                    # Core + dev dependencies
# uv sync --extra all --extra dev      # All deps including docking + deep learning
export EHRLICH_ANTHROPIC_API_KEY=sk-ant-...
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
```

Optional dependency groups:
- `docking` -- AutoDock Vina + Meeko (requires Boost C++ libraries)
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

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/methodology` | Methodology: phases, domains, tools, data sources, models |
| GET | `/api/v1/stats` | Aggregate counts (tools, domains, phases, data sources, events) |
| GET | `/api/v1/investigate` | List all investigations (most recent first) |
| GET | `/api/v1/investigate/{id}` | Full investigation detail |
| POST | `/api/v1/investigate` | Create new investigation |
| GET | `/api/v1/investigate/{id}/stream` | SSE stream of investigation events |
| POST | `/api/v1/investigate/{id}/approve` | Approve/reject formulated hypotheses |
| GET | `/api/v1/molecule/depict?smiles=&w=&h=` | 2D SVG depiction (`image/svg+xml`, cached 24h) |
| GET | `/api/v1/molecule/conformer?smiles=` | 3D conformer (JSON: mol_block, energy, num_atoms) |
| GET | `/api/v1/molecule/descriptors?smiles=` | Molecular descriptors + Lipinski pass/fail |
| GET | `/api/v1/targets` | List protein targets (pdb_id, name, organism) |

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
6. See the Live Lab: 3D molecular scene updates as experiments run -- proteins load, ligands dock, candidates glow by score
7. View ranked candidates with 2D structure thumbnails in the results table
8. Click any candidate row to expand the detail panel with 3D conformer viewer, molecular properties, and Lipinski assessment
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

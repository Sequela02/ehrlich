# Ehrlich

AI-powered molecular discovery engine. Ehrlich uses Claude as a hypothesis-driven scientific reasoning engine combined with cheminformatics, machine learning, molecular simulation, and multi-source data tools to investigate any molecular science question.

Named after Paul Ehrlich, the father of the "magic bullet" -- finding the right molecule for any target.

Built for the [Claude Code Hackathon](https://docs.anthropic.com/en/docs/claude-code-hackathon) (Feb 10-16, 2026).

## What Can Ehrlich Investigate?

Ehrlich is **domain-agnostic**. The hypothesis-driven engine works for any question expressible as "find, analyze, predict, rank molecules":

- **Antimicrobial resistance** -- "Find novel compounds active against MRSA"
- **Drug discovery** -- "What compounds in Lycopodium selago could treat Alzheimer's?"
- **Environmental toxicology** -- "Which microplastic degradation products are most toxic?"
- **Agricultural biocontrol** -- "Find biocontrol molecules from endophytic bacteria in Mammillaria"
- **Antifungal/antiviral** -- "Screen compounds against fungal CYP51"
- **Any molecular target** -- dynamic protein target discovery from 200K+ PDB structures

## Architecture

Ehrlich follows Domain-Driven Design with seven bounded contexts:

| Context | Purpose |
|---------|---------|
| **kernel** | Shared primitives: SMILES, Molecule, exceptions |
| **literature** | Scientific paper search (Semantic Scholar) and reference management |
| **chemistry** | Cheminformatics: molecular descriptors, fingerprints, 3D conformers |
| **analysis** | Dataset exploration (ChEMBL, PubChem), substructure enrichment |
| **prediction** | ML modeling: train, predict, ensemble, cluster |
| **simulation** | Molecular docking, ADMET, resistance, target discovery (RCSB PDB), toxicity (EPA CompTox) |
| **investigation** | Multi-model agent orchestration with Director-Worker-Summarizer pattern |

### Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence, synthesizes (3-5 calls)
Sonnet 4.5 (Researcher) -- Executes experiments with 27 tools (10-20 calls)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs >2000 chars (5-10 calls)
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

All data sources are free and open-access.

## 27 Tools

| Context | Tool | Description |
|---------|------|-------------|
| Chemistry | `validate_smiles` | Validate SMILES string |
| Chemistry | `compute_descriptors` | MW, LogP, TPSA, HBD, HBA, QED, rings |
| Chemistry | `compute_fingerprint` | Morgan (2048-bit) or MACCS (166-bit) |
| Chemistry | `tanimoto_similarity` | Similarity between two molecules (0-1) |
| Chemistry | `generate_3d` | 3D conformer with MMFF94 optimization |
| Chemistry | `substructure_match` | SMARTS/SMILES substructure search |
| Literature | `search_literature` | Semantic Scholar paper search |
| Literature | `get_reference` | Curated reference lookup |
| Analysis | `explore_dataset` | Load ChEMBL bioactivity data for any target |
| Analysis | `search_bioactivity` | Flexible ChEMBL query (any assay type) |
| Analysis | `search_compounds` | PubChem compound search |
| Analysis | `analyze_substructures` | Chi-squared enrichment analysis |
| Analysis | `compute_properties` | Property distributions (active vs inactive) |
| Prediction | `train_model` | Train XGBoost/Chemprop on any SMILES+activity data |
| Prediction | `predict_candidates` | Score compounds with trained model |
| Prediction | `cluster_compounds` | Butina structural clustering |
| Simulation | `search_protein_targets` | RCSB PDB target discovery by organism/function |
| Simulation | `dock_against_target` | AutoDock Vina docking (or RDKit fallback) |
| Simulation | `predict_admet` | Drug-likeness profiling |
| Simulation | `fetch_toxicity_profile` | EPA CompTox environmental toxicity |
| Simulation | `assess_resistance` | Resistance mutation scoring |
| Investigation | `propose_hypothesis` | Register testable hypothesis |
| Investigation | `design_experiment` | Plan experiment with tool sequence |
| Investigation | `evaluate_hypothesis` | Assess outcome with confidence score |
| Investigation | `record_finding` | Record finding linked to hypothesis |
| Investigation | `record_negative_control` | Validate model with known-inactive compounds |
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
| GET | `/api/v1/investigate` | List all investigations (most recent first) |
| GET | `/api/v1/investigate/{id}` | Full investigation detail |
| POST | `/api/v1/investigate` | Create new investigation |
| GET | `/api/v1/investigate/{id}/stream` | SSE stream of investigation events |
| GET | `/api/v1/molecule/depict?smiles=&w=&h=` | 2D SVG depiction (`image/svg+xml`, cached 24h) |
| GET | `/api/v1/molecule/conformer?smiles=` | 3D conformer (JSON: mol_block, energy, num_atoms) |
| GET | `/api/v1/molecule/descriptors?smiles=` | Molecular descriptors + Lipinski pass/fail |
| GET | `/api/v1/targets` | List protein targets (pdb_id, name, organism) |

### SSE Event Types

| Event | Description |
|-------|-------------|
| `hypothesis_formulated` | New hypothesis proposed |
| `experiment_started` | Experiment execution begins |
| `experiment_completed` | Experiment finished with results |
| `hypothesis_evaluated` | Hypothesis outcome assessed |
| `negative_control` | Model validation result |
| `tool_called` | Tool invocation with inputs |
| `tool_result` | Tool output preview |
| `finding_recorded` | Scientific finding captured |
| `thinking` | Model reasoning text |
| `output_summarized` | Haiku compressed a large output |
| `completed` | Investigation finished with candidates and cost |
| `error` | Error occurred |

## Demo

1. Start the server: `cd server && uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`
2. Start the console: `cd console && bun dev`
3. Open http://localhost:5173
4. Type any molecular science research question, for example:
   - *"Find novel antimicrobial candidates against MRSA"*
   - *"What compounds in Lycopodium selago could treat Alzheimer's?"*
   - *"Which microplastic degradation products are most toxic?"*
   - *"Find compounds active against Acinetobacter baumannii"*
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
bun test          # Vitest
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

## License

MIT - see [LICENSE](LICENSE).

## Author

Ricardo Armenta / [Sequel](https://github.com/Sequela02)

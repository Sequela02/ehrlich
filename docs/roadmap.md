# Ehrlich Roadmap

Hackathon: Feb 10-16, 2026. Seven phases, each ending with something testable.

---

## Phase 0: Infrastructure (Day 1) -- DONE

- [x] Git init, LICENSE, README, CLAUDE.md, CHANGELOG
- [x] Server scaffolding: pyproject.toml, uv, all bounded contexts (domain/application/infrastructure/tools)
- [x] Kernel: SMILES/InChIKey/MolBlock types, Molecule value object, exception hierarchy
- [x] API: FastAPI factory, CORS, health endpoint
- [x] Console scaffolding: React 19, TypeScript, Bun, Vite, TanStack Router
- [x] Console features: investigation + molecule component stubs
- [x] CI/CD: GitHub Actions (ruff, mypy, pytest, tsc, vite build)
- [x] Docker: multi-stage builds (server + console)
- [x] Pre-commit: ruff lint + format
- [x] All quality gates passing (ruff 0, mypy 0, pytest 5/5, tsc 0)

**Verification:** `uv run pytest` passes, `GET /api/v1/health` returns 200, `bun run build` succeeds.

---

## Phase 1: Chemistry Context (Day 2)

The foundation. Every other context depends on molecular processing.

### 1A. RDKit Adapter -- Core Operations
- [ ] `validate_smiles(smiles)` -- `Chem.MolFromSmiles`, null-check, return bool
- [ ] `canonicalize(smiles)` -- canonical SMILES via RDKit
- [ ] `to_inchikey(smiles)` -- SMILES -> InChI -> InChIKey (needed for Tox21 cross-ref)
- [ ] Tests: valid/invalid SMILES, canonicalization consistency

### 1B. RDKit Adapter -- Descriptors & Fingerprints
- [ ] `compute_descriptors(smiles)` -- MW, LogP, TPSA, HBD, HBA, RotatableBonds, QED, NumRings
- [ ] `compute_fingerprint(smiles, fp_type)` -- Morgan/ECFP (radius=2, 2048-bit) + MACCS (166-bit)
- [ ] `tanimoto_similarity(fp1, fp2)` -- similarity score (0.0-1.0)
- [ ] Tests: aspirin descriptors match known values, fingerprint bit counts

### 1C. RDKit Adapter -- 3D & Substructure
- [ ] `generate_conformer(smiles)` -- AddHs, EmbedMolecule(ETKDGv3), MMFFOptimize, MolToMolBlock
- [ ] `substructure_match(smiles, pattern)` -- returns bool + matching atom indices
- [ ] Tests: 3D conformer has coordinates, substructure match on known patterns

### 1D. Chemistry Service + Tools
- [ ] Wire `ChemistryService` to `RDKitAdapter` via dependency injection
- [ ] Implement `generate_3d` tool -- SMILES -> JSON with MolBlock + energy
- [ ] Implement `substructure_match` tool -- SMILES + pattern -> JSON with match + atoms
- [ ] Implement `modify_molecule` tool -- stub (R-group enumeration, stretch goal)
- [ ] Tests: service integration tests, tool JSON output validation

**Verification:** `uv run pytest tests/chemistry/ -v` all pass, mypy clean.

---

## Phase 2: Literature + Analysis (Day 2-3)

Two independent contexts. Can be built in parallel.

### 2A. Semantic Scholar Client
- [ ] HTTP client with `httpx` -- search endpoint (`/graph/v1/paper/search`)
- [ ] Parse response: title, authors, year, abstract, DOI, citationCount
- [ ] Rate limiting: respect 100 req/sec unauthenticated limit
- [ ] Error handling: timeout, 429 rate limit, malformed response
- [ ] Tests: mock HTTP responses, verify Paper entity construction

### 2B. PubMed Client (Backup)
- [ ] Two-step: esearch (get PMIDs) -> efetch (get details)
- [ ] Parse XML response into Paper entities
- [ ] Tests: mock XML responses

### 2C. Core Reference Set
- [ ] Load `data/references/core_references.json` into `CoreReferenceSet`
- [ ] Lookup by key: halicin, abaucin, who_bppl_2024, chemprop, pkcsm
- [ ] Expand JSON with full metadata (key findings, training size, hit rates)
- [ ] Tests: load fixture, find by DOI, find by key

### 2D. Literature Service + Tools
- [ ] `search_papers(query, limit)` -- Semantic Scholar primary, PubMed fallback
- [ ] `get_reference(key)` -- core reference lookup
- [ ] `format_citation(paper)` -- APA-style string
- [ ] Implement `search_literature` tool -- query -> JSON with papers
- [ ] Implement `get_reference` tool -- key -> JSON with full citation
- [ ] Tests: service with mock repos, tool JSON output

### 2E. ChEMBL Loader
- [ ] HTTP client for ChEMBL API (`chembl_webresource_client` or direct REST)
- [ ] Filter by: target_organism, standard_type=MIC, standard_relation="="
- [ ] Deduplicate: one entry per SMILES (median activity if duplicates)
- [ ] Compute pActivity: -log10(standard_value * 1e-6) when not available
- [ ] Generate InChIKeys via chemistry context (kernel primitives)
- [ ] Build `Dataset` entity: smiles_list, activities, metadata
- [ ] Tests: mock API, verify filtering/dedup logic

### 2F. Tox21 Loader
- [ ] Load Tox21 CSV (DeepChem format or direct download)
- [ ] Parse 12 toxicity endpoints (NR-AR through SR-p53)
- [ ] Generate InChIKeys for cross-referencing
- [ ] `cross_reference(dataset)` -- merge ChEMBL + Tox21 on InChIKey
- [ ] Tests: fixture CSV, verify parsing and cross-ref

### 2G. Analysis Service + Tools
- [ ] `explore(target, threshold)` -- load dataset, return stats (size, active count, distributions)
- [ ] `analyze_substructures(dataset)` -- enrichment analysis on fingerprint bits, chi-squared p-values
- [ ] `compute_properties(dataset)` -- descriptor distributions across active vs inactive
- [ ] Implement `explore_dataset` tool -- target -> JSON with stats
- [ ] Implement `analyze_substructures` tool -- target -> JSON with enriched substructures
- [ ] Implement `compute_properties` tool -- target -> JSON with property distributions
- [ ] Tests: mock datasets, verify enrichment logic, property computation

**Verification:** `uv run pytest tests/literature/ tests/analysis/ -v` all pass.

---

## Phase 3: Prediction Context (Day 3-4)

ML models for antimicrobial activity prediction.

### 3A. XGBoost Adapter
- [ ] Train: Morgan fingerprints (2048-bit) + activities -> XGBoost classifier
- [ ] Scaffold split: train/val/test by Murcko scaffold (prevents data leakage)
- [ ] Metrics: AUROC, AUPRC, accuracy, F1, confusion matrix
- [ ] Feature importance: top fingerprint bits -> interpret as substructures
- [ ] Predict: fingerprints -> probabilities
- [ ] Tests: small fixture dataset, verify model trains and predicts

### 3B. Model Store
- [ ] Save: `TrainedModel` metadata + joblib artifact -> disk
- [ ] Load: model_id -> `TrainedModel` + artifact
- [ ] List: all saved models with metrics
- [ ] Tests: save/load roundtrip

### 3C. Prediction Service -- Train & Predict
- [ ] `train(target, model_type)` -- load dataset, compute fingerprints, scaffold split, train, save
- [ ] `predict(smiles_list, model_id)` -- load model, compute fingerprints, predict, rank
- [ ] `cluster(smiles_list, n_clusters)` -- Butina clustering on Tanimoto distances
- [ ] Tests: full train -> predict pipeline with fixture data

### 3D. Chemprop Adapter (Optional Extra)
- [ ] Train: SMILES + activities -> Chemprop D-MPNN (requires `deeplearning` extra)
- [ ] Predict: SMILES -> probabilities
- [ ] Guard: graceful skip if chemprop not installed
- [ ] Tests: mock or skip if extra not available

### 3E. Ensemble & Tools
- [ ] `ensemble(smiles_list)` -- average XGBoost + Chemprop (0.5 each), fallback to single
- [ ] Implement `train_model` tool -- target + model_type -> JSON with metrics
- [ ] Implement `predict_candidates` tool -- smiles_list + model_id -> JSON with ranked predictions
- [ ] Implement `cluster_compounds` tool -- smiles_list -> JSON with clusters
- [ ] Tests: ensemble logic, tool JSON output

**Verification:** `uv run pytest tests/prediction/ -v` all pass. Can train on fixture data.

---

## Phase 4: Simulation Context (Day 4)

Molecular docking, ADMET prediction, resistance assessment.

### 4A. Protein Store
- [ ] Manage PDBQT files in `data/proteins/`
- [ ] Target registry: PDB ID -> name, organism, center coordinates, box size
- [ ] Pre-configure 5 MRSA targets: PBP2a (1VQQ), DHPS (1AD4), DNA Gyrase (2XCT), MurA (1UAE), NDM-1 (3SPU)
- [ ] `get_pdbqt(pdb_id)` -- return file path or download
- [ ] Tests: target lookup, file existence check

### 4B. Vina Adapter (Optional Extra)
- [ ] Dock: SMILES -> conformer (RDKit) -> Meeko prep -> Vina dock -> energy + pose
- [ ] Parse results: binding energy (kcal/mol), best pose PDBQT, RMSD
- [ ] Interpret energy: excellent (<= -10), strong (-8 to -10), moderate (-6 to -8), weak (> -6)
- [ ] Guard: graceful skip if vina/meeko not installed
- [ ] Tests: mock Vina, verify result structure

### 4C. ADMET Client
- [ ] pkCSM API client: SMILES -> absorption, distribution, metabolism, excretion, toxicity
- [ ] SwissADME API client (backup)
- [ ] RDKit fallback: compute descriptors + Lipinski + QED when APIs unavailable
- [ ] Build `ADMETProfile` from API or fallback results
- [ ] Toxicity flags: Ames, hERG, hepatotoxicity
- [ ] Tests: mock API responses, verify profile construction, fallback logic

### 4D. Resistance Assessment
- [ ] Dock wild-type + mutant targets for same compound
- [ ] Compare binding energies: delta > 2.0 = HIGH risk, > 1.0 = MODERATE, else LOW
- [ ] Known mutations: PBP2a S403A/N146K, DHPS F17L, DNA Gyrase S84L
- [ ] Build `ResistanceAssessment` with per-mutation risk
- [ ] Tests: mock docking results, verify risk classification

### 4E. Simulation Service + Tools
- [ ] `dock(smiles, target_id)` -- full docking pipeline
- [ ] `predict_admet(smiles)` -- API with fallback
- [ ] `assess_resistance(smiles, target_id)` -- wild-type vs mutant docking
- [ ] Implement `dock_against_target` tool -- smiles + target -> JSON with energy + pose
- [ ] Implement `predict_admet` tool -- smiles -> JSON with ADMET profile
- [ ] Implement `assess_resistance` tool -- smiles + target -> JSON with mutation risks
- [ ] Tests: service integration tests, tool JSON output

**Verification:** `uv run pytest tests/simulation/ -v` all pass.

---

## Phase 5: Investigation Agent (Day 4-5)

The core: Claude as an autonomous scientist.

### 5A. Anthropic Client Adapter
- [ ] Wrap `anthropic.Anthropic().messages.create()` -- isolate SDK dependency
- [ ] Handle: system prompt, messages array, tools list, max_tokens
- [ ] Parse response: content blocks (text, tool_use), stop_reason, usage
- [ ] Error handling: rate limits, API errors, timeout
- [ ] Tests: mock API, verify request/response handling

### 5B. Tool Registry
- [ ] Register all 16 tools from all contexts
- [ ] Auto-generate JSON Schema from Python type hints + docstrings
- [ ] `get(name)` -> callable, `list_tools()` -> all registered tools
- [ ] Schema format matches Anthropic tool_use specification
- [ ] Tests: register tool, verify schema generation, lookup

### 5C. Cost Tracker
- [ ] Track per-run: input_tokens, output_tokens, tool_calls count
- [ ] Compute cost: Sonnet 4.5 pricing ($3/M input, $15/M output)
- [ ] Running totals across iterations
- [ ] Tests: add_usage, verify total_cost calculation

### 5D. System Prompt
- [ ] Scientist persona: methodology, phases, rules
- [ ] 7 research phases: literature review, data exploration, model training, virtual screening, structural analysis, resistance assessment, conclusions
- [ ] Constraints: minimum 3 tools per phase, always cite references, record findings
- [ ] Output format: structured findings + ranked candidates + citations

### 5E. Orchestrator -- Agentic Loop
- [ ] Create `Investigation` entity, set status to RUNNING
- [ ] Build messages array: system prompt + user research question
- [ ] Loop: call Claude -> check stop_reason -> dispatch tool_use -> collect results -> repeat
- [ ] Max iteration guard (configurable, default 50)
- [ ] Emit domain events: PhaseStarted, ToolCalled, FindingRecorded, InvestigationCompleted
- [ ] Handle: parallel tool calls (Claude can request multiple), tool errors
- [ ] End condition: stop_reason == "end_turn" or max iterations
- [ ] Tests: mock Claude responses with tool_use, verify dispatch + event emission

### 5F. SSE Streaming
- [ ] Convert domain events to SSE events (SSEEventType enum)
- [ ] Wire orchestrator events to `sse-starlette` EventSourceResponse
- [ ] Event types: phase_started, tool_called, tool_result, finding_recorded, thinking, error, completed
- [ ] Include cost tracker data in completed event

### 5G. Investigation API Routes
- [ ] `POST /api/v1/investigate` -- accept prompt, create investigation, return ID
- [ ] `GET /api/v1/investigate/{id}/stream` -- SSE stream of orchestrator events
- [ ] Request/response DTOs with Pydantic models
- [ ] Error handling: invalid ID, investigation already running
- [ ] Tests: FastAPI TestClient, mock orchestrator

### 5H. Control Tools
- [ ] `record_finding(title, detail, evidence, phase)` -- store finding in investigation
- [ ] `conclude_investigation(summary, candidates, citations)` -- end investigation, return results
- [ ] Tests: verify finding storage, conclusion structure

**Verification:** Can run a full investigation via `POST /investigate` and receive SSE stream. `uv run pytest tests/investigation/ tests/api/ -v` all pass.

---

## Phase 6: Console Integration (Day 5-6)

Visualization and real-time streaming UI.

### 6A. RDKit.js WASM Integration
- [ ] `useRDKit` hook: async WASM init, loading state, error handling
- [ ] Memory management: `mol.delete()` cleanup on unmount
- [ ] Tests: hook renders without crash

### 6B. Molecule Viewers
- [ ] `MolViewer2D`: RDKit.js `get_svg()` with substructure highlighting
- [ ] `MolViewer3D`: 3Dmol.js WebGL viewer, load MolBlock from backend
- [ ] `DockingViewer`: 3Dmol.js protein (PDB) + ligand (MolBlock) overlay
- [ ] `PropertyCard`: display descriptors, QED, Lipinski pass/fail

### 6C. Investigation Flow
- [ ] Wire `PromptInput` to `useInvestigation` mutation (POST /investigate)
- [ ] Navigate to `/investigation/$id` on success
- [ ] `useSSE` hook: connect to `/api/v1/investigate/{id}/stream`
- [ ] `Timeline`: render SSE events in real-time (phases, tool calls, findings)
- [ ] `CandidateTable`: populate from findings/conclusion events
- [ ] `ReportViewer`: render markdown summary from conclude event
- [ ] `CostBadge`: live token/cost from SSE events

### 6D. Polish
- [ ] Loading states: skeleton loaders during WASM init and API calls
- [ ] Error states: connection lost, API errors, empty states
- [ ] Responsive layout: works on desktop widths (1024+)
- [ ] Tests: component rendering with mock data

**Verification:** Full flow works in browser: enter prompt -> see timeline -> view candidates -> read report.

---

## Phase 7: Integration + Demo (Day 6-7)

### 7A. End-to-End Validation
- [ ] Run real investigation: "Find novel antimicrobial candidates against MRSA"
- [ ] Verify: literature citations are real (DOIs resolve)
- [ ] Verify: ChEMBL data loads and filters correctly
- [ ] Verify: ML model trains and produces reasonable AUROC (> 0.7)
- [ ] Verify: docking energies in expected range
- [ ] Verify: ADMET profiles have no None values
- [ ] Verify: cost tracking matches expected (~$0.13 for 5 iterations on Sonnet)
- [ ] Fix any integration issues discovered

### 7B. Data Preparation
- [ ] Download real ChEMBL data for S. aureus (15-20K compounds)
- [ ] Prepare PDBQT files for 5 MRSA targets
- [ ] Verify Tox21 cross-reference produces overlap
- [ ] Cache datasets in `data/datasets/`

### 7C. Error Handling Sweep
- [ ] Graceful degradation: skip docking if vina not installed
- [ ] Graceful degradation: skip Chemprop if torch not installed
- [ ] API fallbacks: RDKit descriptors if pkCSM/SwissADME down
- [ ] Agent loop: handle tool errors without crashing investigation
- [ ] Console: show errors inline, don't break UI

### 7D. Documentation
- [ ] Update README with real demo output
- [ ] Architecture docs: final dependency diagram
- [ ] API docs: endpoint descriptions + example requests
- [ ] Contributing guide (for post-hackathon)

### 7E. Demo
- [ ] Record terminal demo: start server, run investigation, show results
- [ ] Record browser demo: full console flow with molecule viewers
- [ ] GitHub repo: clean history, proper description, tags

**Verification:** Clean demo run, all quality gates green, repo ready for submission.

---

## Dependency Graph

```
Phase 0 (Infrastructure) -- DONE
    |
Phase 1 (Chemistry)
    |         \
Phase 2A-D    Phase 2E-G
(Literature)  (Analysis)
    |              |
    +----- + ------+
           |
     Phase 3 (Prediction)
           |
     Phase 4 (Simulation) -- can parallel with late Phase 3
           |
     Phase 5 (Agent Loop)
           |
     Phase 6 (Console)
           |
     Phase 7 (Integration + Demo)
```

## Post-Hackathon

- MCP server for external Claude Code / Claude Desktop clients
- Multi-investigation management (history, comparison)
- Compound library persistence (SQLite/PostgreSQL)
- Batch screening mode (score entire ZINC subsets)
- Additional organisms: E. coli, P. aeruginosa, A. baumannii, M. tuberculosis
- Antifungal/antiviral expansion
- Automated synthesis lab integration (Emerald Cloud Lab, Strateos)
- Community contributions: new tools, new targets, new models

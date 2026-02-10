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

## Phase 1: Chemistry Context (Day 2) -- DONE

The foundation. Every other context depends on molecular processing.

### 1A. RDKit Adapter -- Core Operations
- [x] `validate_smiles(smiles)` -- `Chem.MolFromSmiles`, null-check, return bool
- [x] `canonicalize(smiles)` -- canonical SMILES via RDKit
- [x] `to_inchikey(smiles)` -- SMILES -> InChI -> InChIKey (needed for Tox21 cross-ref)
- [x] Tests: valid/invalid SMILES, canonicalization consistency (24 tests)

### 1B. RDKit Adapter -- Descriptors & Fingerprints
- [x] `compute_descriptors(smiles)` -- MW, LogP, TPSA, HBD, HBA, RotatableBonds, QED, NumRings
- [x] `compute_fingerprint(smiles, fp_type)` -- Morgan/ECFP (radius=2, 2048-bit) + MACCS (166-bit)
- [x] `tanimoto_similarity(fp1, fp2)` -- similarity score (0.0-1.0)
- [x] Tests: aspirin descriptors match known values, fingerprint bit counts

### 1C. RDKit Adapter -- 3D & Substructure
- [x] `generate_conformer(smiles)` -- AddHs, EmbedMolecule(ETKDGv3), MMFFOptimize, MolToMolBlock
- [x] `substructure_match(smiles, pattern)` -- returns bool + matching atom indices
- [x] Tests: 3D conformer has coordinates, substructure match on known patterns

### 1D. Chemistry Service + Tools
- [x] Wire `ChemistryService` to `RDKitAdapter` via dependency injection
- [x] Implement `generate_3d` tool -- SMILES -> JSON with MolBlock + energy
- [x] Implement `substructure_match` tool -- SMILES + pattern -> JSON with match + atoms
- [x] Implement `modify_molecule` tool -- stub (R-group enumeration, stretch goal)
- [x] Added `validate_smiles`, `compute_descriptors`, `compute_fingerprint`, `tanimoto_similarity` tools
- [x] Tests: service integration tests (9), tool JSON output validation (11)

**Verification:** `uv run pytest tests/chemistry/ -v` -- 44 passed, mypy clean.

---

## Phase 2: Literature + Analysis (Day 2-3) -- DONE

Two independent contexts. Can be built in parallel.

### 2A. Semantic Scholar Client
- [x] HTTP client with `httpx` -- search endpoint (`/graph/v1/paper/search`)
- [x] Parse response: title, authors, year, abstract, DOI, citationCount
- [x] Rate limiting: respect 100 req/sec unauthenticated limit
- [x] Error handling: timeout, 429 rate limit, malformed response
- [x] Tests: Paper entity construction from API response (3 tests)

### 2B. PubMed Client (Backup)
- [x] Two-step: esearch (get PMIDs) -> efetch (get details)
- [x] Parse XML response into Paper entities
- [ ] Tests: mock XML responses (deferred -- PubMed is fallback only)

### 2C. Core Reference Set
- [x] Load `data/references/core_references.json` into `CoreReferenceSet`
- [x] Lookup by key: halicin, abaucin, who_bppl_2024, chemprop, pkcsm, amr_crisis
- [x] Expanded JSON with full metadata (key findings, training size, hit rates)
- [x] Tests: load fixture, find by key, all 6 keys verified

### 2D. Literature Service + Tools
- [x] `search_papers(query, limit)` -- Semantic Scholar primary, PubMed fallback
- [x] `get_reference(key)` -- core reference lookup + DOI fallback
- [x] `format_citation(paper)` -- APA-style string
- [x] Implement `search_literature` tool -- query -> JSON with papers
- [x] Implement `get_reference` tool -- key -> JSON with full citation
- [x] Tests: service with mock repos (8), tool JSON output (3)

### 2E. ChEMBL Loader
- [x] HTTP client for ChEMBL REST API (direct httpx)
- [x] Filter by: target_organism, standard_type=MIC/IC50, standard_relation="="
- [x] Deduplicate: one entry per SMILES (median activity if duplicates)
- [x] Compute pActivity: -log10(standard_value * 1e-6)
- [x] Parquet caching for downloaded datasets
- [x] Build `Dataset` entity: smiles_list, activities, metadata
- [ ] Tests: mock API (deferred -- uses mock service in tools tests)

### 2F. Tox21 Loader
- [x] Load Tox21 CSV with 12 toxicity endpoints
- [x] Parse 12 toxicity endpoints (NR-AR through SR-p53)
- [x] `cross_reference(dataset)` -- compute SMILES overlap
- [ ] Tests: fixture CSV (deferred -- needs dataset download)

### 2G. Analysis Service + Tools
- [x] `explore(target, threshold)` -- load dataset, return stats
- [x] `analyze_substructures(dataset)` -- chi-squared enrichment on 10 known substructures
- [x] `compute_properties(dataset)` -- descriptor distributions (active vs inactive)
- [x] Implement `explore_dataset` tool -- target -> JSON with stats
- [x] Implement `analyze_substructures` tool -- target -> JSON with enriched substructures
- [x] Implement `compute_properties` tool -- target -> JSON with property distributions
- [x] Tests: mock datasets (6), enrichment logic, property computation, tool output (3)

**Verification:** `uv run pytest tests/literature/ tests/analysis/ -v` -- 23 passed.

---

## Phase 3: Prediction Context (Day 3-4) -- DONE

ML models for antimicrobial activity prediction.

### 3A. XGBoost Adapter
- [x] Train: Morgan fingerprints (2048-bit) + activities -> XGBoost classifier
- [x] Scaffold split: train/val/test by Murcko scaffold (prevents data leakage)
- [x] Metrics: AUROC, AUPRC, accuracy, F1, confusion matrix
- [x] Feature importance: top fingerprint bits -> interpret as substructures
- [x] Predict: fingerprints -> probabilities
- [x] Tests: small fixture dataset, verify model trains and predicts (5 tests)

### 3B. Model Store
- [x] Save: `TrainedModel` metadata + joblib artifact -> disk
- [x] Load: model_id -> `TrainedModel` + artifact
- [x] List: all saved models with metrics
- [x] Tests: save/load roundtrip (4 tests)

### 3C. Prediction Service -- Train & Predict
- [x] `train(target, model_type)` -- load dataset, compute fingerprints, scaffold split, train, save
- [x] `predict(smiles_list, model_id)` -- load model, compute fingerprints, predict, rank
- [x] `cluster(smiles_list, n_clusters)` -- Butina clustering on Tanimoto distances
- [x] Tests: full train -> predict pipeline with fixture data (8 tests)

### 3D. Chemprop Adapter (Optional Extra)
- [x] Train: SMILES + activities -> Chemprop D-MPNN (requires `deeplearning` extra)
- [x] Predict: SMILES -> probabilities
- [x] Guard: graceful skip if chemprop not installed
- [x] Tests: mock or skip if extra not available

### 3E. Ensemble & Tools
- [x] `ensemble(smiles_list)` -- average XGBoost + Chemprop (0.5 each), fallback to single
- [x] Implement `train_model` tool -- target + model_type -> JSON with metrics
- [x] Implement `predict_candidates` tool -- smiles_list + model_id -> JSON with ranked predictions
- [x] Implement `cluster_compounds` tool -- smiles_list -> JSON with clusters
- [x] Tests: ensemble logic, tool JSON output (3 tests)

**Verification:** `uv run pytest tests/prediction/ -v` -- 20 passed, mypy clean.

---

## Phase 4: Simulation Context (Day 4) -- DONE

Molecular docking, ADMET prediction, resistance assessment.

### 4A. Protein Store
- [x] Manage PDBQT files in `data/proteins/`
- [x] Target registry: PDB ID -> name, organism, center coordinates, box size
- [x] Pre-configure 5 MRSA targets: PBP2a (1VQQ), DHPS (1AD4), DNA Gyrase (2XCT), MurA (1UAE), NDM-1 (3SPU)
- [x] `get_pdbqt(pdb_id)` -- return file path or download
- [x] Tests: target lookup, file existence check (6 tests)

### 4B. Vina Adapter (Optional Extra)
- [x] Dock: SMILES -> conformer (RDKit) -> Meeko prep -> Vina dock -> energy + pose
- [x] Parse results: binding energy (kcal/mol), best pose PDBQT, RMSD
- [x] Interpret energy: excellent (<= -10), strong (-8 to -10), moderate (-6 to -8), weak (> -6)
- [x] Guard: graceful skip if vina/meeko not installed
- [x] Tests: energy interpretation (6 tests in protein_store)

### 4C. ADMET Client
- [x] RDKit-based ADMET: Lipinski violations, mutagenic alerts (SMARTS), hepatotoxicity, hERG, BBB
- [x] Build `ADMETProfile` with absorption, distribution_vd, metabolism, excretion, toxicity
- [x] Toxicity flags: Ames (nitro/azide/quinone alerts), hERG (LogP + MW), hepatotoxicity (LogP + MW + acyl chloride/thioester)
- [x] Tests: aspirin profile, ethanol BBB, nitroaromatic mutagenic, hepatotoxic compound (5 tests)

### 4D. Resistance Assessment
- [x] Knowledge-based mutation risk with compound class pattern matching
- [x] Known mutations: PBP2a S403A/N146K, DHPS F17L, DNA Gyrase S84L, MurA C115D, NDM-1 V73_ins/M154L
- [x] Compound class patterns: beta-lactam ring, fluoroquinolone, sulfonamide -> affected targets
- [x] Build `ResistanceAssessment` with per-mutation `MutationRisk` and overall risk level
- [x] Tests: known target mutations, DNA gyrase, mutations dict (3 tests in simulation_service)

### 4E. Simulation Service + Tools
- [x] `dock(smiles, target_id)` -- Vina with RDKit descriptor-based estimate fallback
- [x] `predict_admet(smiles)` -- RDKit-based via PkCSMClient
- [x] `assess_resistance(smiles, target_id)` -- knowledge-based with compound class risk
- [x] Implement `dock_against_target` tool -- smiles + target -> JSON with energy + interpretation
- [x] Implement `predict_admet` tool -- smiles -> JSON with ADMET profile + toxicity flags
- [x] Implement `assess_resistance` tool -- smiles + target -> JSON with mutation details
- [x] Tests: service integration (6), tool JSON output (3)

**Verification:** `uv run pytest tests/simulation/ -v` -- 20 passed, mypy clean.

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
Phase 1 (Chemistry) -- DONE
    |         \
Phase 2A-D    Phase 2E-G
(Literature)  (Analysis)  -- DONE
    |              |
    +----- + ------+
           |
     Phase 3 (Prediction) -- DONE
           |
     Phase 4 (Simulation) -- DONE
           |
     Phase 5 (Agent Loop) <-- NEXT
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

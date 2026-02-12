# Ehrlich Roadmap

Hackathon: Feb 10-16, 2026. Each phase ends with something testable.

---

## Phase 0: Infrastructure (Feb 10) -- DONE

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

## Phase 1: Chemistry Context (Feb 10) -- DONE

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

## Phase 2: Literature + Analysis (Feb 10) -- DONE

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

## Phase 3: Prediction Context (Feb 10) -- DONE

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

## Phase 4: Simulation Context (Feb 10) -- DONE

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

## Phase 5: Investigation Agent (Feb 10) -- DONE

The core: Claude as an autonomous scientist.

### 5A. Anthropic Client Adapter
- [x] Wrap `anthropic.AsyncAnthropic().messages.create()` -- isolate SDK dependency
- [x] Handle: system prompt, messages array, tools list, max_tokens
- [x] Parse response: content blocks (text, tool_use), stop_reason, usage
- [x] Error handling: rate limits, API errors, timeout
- [x] Tests: mock API, verify request/response handling

### 5B. Tool Registry
- [x] Register all tools from all contexts (6 chemistry, 3 literature, 6 analysis, 3 prediction, 7 simulation, 6 sports, 7 investigation control -- 38 total)
- [x] Auto-generate JSON Schema from Python type hints + docstrings
- [x] `get(name)` -> callable, `list_tools()` -> all registered tools, `list_schemas()` -> Anthropic-compatible schemas
- [x] Schema format matches Anthropic tool_use specification
- [x] Tests: register tool, verify schema generation, lookup, list params, defaults (8 tests)

### 5C. Cost Tracker
- [x] Track per-run: input_tokens, output_tokens, tool_calls count
- [x] Compute cost: Sonnet 4.5 pricing ($3/M input, $15/M output)
- [x] Running totals across iterations, `to_dict()` for serialization
- [x] Tests: add_usage, verify total_cost calculation (6 tests)

### 5D. System Prompt
- [x] Scientist persona: Paul Ehrlich, methodology, phases, rules
- [x] 7 research phases with specific tool guidance per phase
- [x] Constraints: minimum 3 tools per phase, always cite references, record findings
- [x] Output format: structured findings + ranked candidates + citations

### 5E. Orchestrator -- Agentic Loop
- [x] Create `Investigation` entity, set status to RUNNING
- [x] Build messages array: system prompt + user research question
- [x] Loop: call Claude -> check stop_reason -> dispatch tool_use -> collect results -> repeat
- [x] Max iteration guard (configurable, default 50)
- [x] Emit domain events: HypothesisFormulated, ExperimentStarted, ExperimentCompleted, HypothesisEvaluated, NegativeControlRecorded, ToolCalled, ToolResultEvent, FindingRecorded, Thinking, InvestigationCompleted, InvestigationError
- [x] Handle: parallel tool calls (Claude can request multiple), tool errors (graceful JSON error return)
- [x] End condition: stop_reason == "end_turn", conclude_investigation called, or max iterations
- [x] Phase auto-detection from tool names
- [x] Tests: mock Claude responses with tool_use, verify dispatch + event emission (9 tests)

### 5F. SSE Streaming
- [x] Convert domain events to SSE events via `domain_event_to_sse()` mapper
- [x] Wire orchestrator async generator to `sse-starlette` EventSourceResponse
- [x] Event types: hypothesis_formulated, experiment_started, experiment_completed, hypothesis_evaluated, negative_control, tool_called, tool_result, finding_recorded, thinking, error, completed, output_summarized
- [x] Include cost tracker data in completed event
- [x] Tests: all 12 event type conversions + JSON format (14 tests)

### 5G. Investigation API Routes
- [x] `POST /api/v1/investigate` -- accept prompt, create investigation, return ID
- [x] `GET /api/v1/investigate/{id}/stream` -- SSE stream of orchestrator events
- [x] Request/response DTOs with Pydantic models (InvestigateRequest, InvestigateResponse)
- [x] Error handling: 404 invalid ID, 409 investigation already running
- [x] Tests: FastAPI TestClient (4 tests)

### 5H. Control Tools
- [x] `record_finding(title, detail, hypothesis_id, evidence_type)` -- orchestrator intercepts and stores in Investigation entity
- [x] `conclude_investigation(summary, candidates, citations)` -- orchestrator intercepts, sets candidates/citations, ends loop
- [x] `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_negative_control` -- hypothesis control tools
- [x] Tests: verify finding storage, conclusion structure, hypothesis tools (10 tests)

**Verification:** `uv run pytest tests/investigation/ tests/api/ -v` -- 41 passed. Full suite 153 passed, 82% coverage, ruff 0, mypy 0.

---

## Phase 6: Console Integration (Feb 10) -- DONE

Visualization and real-time streaming UI.

### 6A. ~~RDKit.js WASM Integration~~ (Replaced by server-side SVG)
- [x] Replaced with server-side RDKit `rdMolDraw2D` SVG depiction (higher quality, simpler)
- [x] Deleted `useRDKit` hook (dead code)

### 6B. Molecule Viewers
- [x] `MolViewer2D`: server-side SVG via `<img src="/api/v1/molecule/depict">`, lazy loading, error fallback
- [x] `MolViewer3D`: 3Dmol.js WebGL viewer with stick style, Jmol coloring, dynamic import
- [x] `DockingViewer`: 3Dmol.js protein cartoon (spectrum) + ligand stick (green carbon) overlay
- [x] `PropertyCard`: display descriptors with generic property grid

### 6C. Investigation Flow
- [x] Wire `PromptInput` to `useInvestigation` mutation (POST /investigate)
- [x] Navigate to `/investigation/$id` on success
- [x] `useSSE` hook: named event listeners for all 7 SSE event types, parsed state (currentPhase, findings, summary, cost, error)
- [x] `Timeline`: rich rendering per event type with phase icons, tool call previews, finding highlights
- [x] `FindingsPanel`: sidebar panel showing accumulated findings with phase badges
- [x] `CandidateTable`: populate from conclusion event data
- [x] `ReportViewer`: render markdown summary from conclude event
- [x] `CostBadge`: live token/cost from SSE completed event

### 6D. Polish
- [x] Loading states: spinner on connecting, "Starting..." on submit
- [x] Error states: connection lost, API errors, inline error messages
- [x] Responsive layout: 3-column grid on desktop (timeline + report | findings + candidates)
- [x] Status indicator: connecting / running (animated) / completed / error
- [x] Auto-scroll timeline to latest event
- [x] Tests: component rendering with mock data (14 tests across 4 files)

**Verification:** `npx vitest run` -- 19 passed. `bun run build` + `tsc --noEmit` -- zero errors.

---

## Phase 7: Integration + Demo (Feb 10) -- DONE

### 7A. End-to-End Validation
- [x] E2E smoke test exercising full pipeline (tool registry, orchestrator dispatch, SSE events)
- [x] API key wired from Settings to AnthropicClientAdapter
- [x] Exponential backoff retry (3 attempts) for rate-limit and timeout errors

### 7B. Data Preparation
- [x] Data preparation script (`data/scripts/prepare_data.py`) for ChEMBL + PDB downloads
- [x] Parquet caching in `data/datasets/`

### 7C. Error Handling Sweep
- [x] Graceful degradation: skip docking if vina not installed
- [x] Graceful degradation: skip Chemprop if torch not installed
- [x] Improved error handling in explore_dataset, train_model, predict_candidates, dock_against_target, assess_resistance
- [x] Agent loop: handle tool errors without crashing investigation

### 7D. Documentation
- [x] README: environment variables, demo instructions, API endpoints
- [x] Architecture and roadmap docs

**Verification:** 160 tests, 81.67% coverage, all quality gates green.

---

## Phase 8: Multi-Model Architecture + Polish (Feb 10) -- DONE

Cost-efficient multi-model orchestration, persistence, and UI polish.

### 8A. Domain Foundation + Config
- [x] Domain events: `OutputSummarized` (kept), hypothesis/experiment events (added in Phase 10A)
- [x] `created_at` and `cost_data` fields on Investigation entity
- [x] Per-model config settings: director, researcher, summarizer models
- [x] `summarizer_threshold`, `max_iterations_per_experiment`, `db_path` settings

### 8B. Multi-Model Cost Tracker
- [x] Per-model usage tracking with model-specific pricing
- [x] Pricing dict: Opus $15/$75, Sonnet $3/$15, Haiku $0.80/$4 per M tokens
- [x] `to_dict()` with `by_model` breakdown (director/researcher/summarizer tiers)
- [x] `AnthropicClientAdapter.model` property for cost attribution

### 8C. Multi-Model Orchestrator
- [x] `MultiModelOrchestrator` with hypothesis-driven Director-Worker-Summarizer pattern
- [x] Director (Opus) formulates hypotheses, designs experiments, evaluates evidence, synthesizes -- NO tool access
- [x] Researcher (Sonnet) executes experiments with 38 domain-filtered tools (max 10 iterations per experiment)
- [x] Summarizer (Haiku) compresses large outputs exceeding threshold
- [x] 7 prompts: director formulation/experiment/evaluation/synthesis, researcher experiment, scientist, summarizer
- [x] Auto-fallback to single-model Orchestrator when researcher == director
- [x] Tests: 12 tests across 8 classes (formulation, execution, evaluation, negative controls, compression, synthesis, full flow, errors)

### 8D. SQLite Persistence
- [x] `InvestigationRepository` ABC in domain layer
- [x] `SqliteInvestigationRepository` with WAL mode via `aiosqlite`
- [x] Single `investigations` table with JSON serialization for complex fields
- [x] Tests: 8 tests (save, retrieve, list, update, cost data)

### 8E. API Wiring
- [x] `GET /investigate` -- list all investigations (most recent first)
- [x] `GET /investigate/{id}` -- full investigation detail
- [x] SQLite repository initialization in app lifespan
- [x] Automatic orchestrator selection (multi-model vs single-model)
- [x] SSE event types: `hypothesis_formulated`, `experiment_started`, `experiment_completed`, `hypothesis_evaluated`, `negative_control`, `output_summarized`
- [x] `completed` event includes candidates and cost data

### 8F. SSE Reconnection
- [x] Exponential backoff (1s, 2s, 4s) with max 3 retries
- [x] `reconnecting` state with amber WiFi-off indicator
- [x] Reset attempt counter on successful reconnect
- [x] Track `experiments`, `hypotheses`, `negativeControls` and `toolCallCount` from events

### 8G. Investigation History
- [x] `useInvestigations` hook with TanStack Query (10s refetch)
- [x] `InvestigationList` component with status badges and candidate counts
- [x] History section on home page below prompt input

### 8H. UI Feedback
- [x] `HypothesisBoard` kanban-style grid with status columns and confidence bars
- [x] Hypothesis/experiment event rendering in Timeline
- [x] Candidates wired to `CandidateTable` from SSE completed event
- [x] `StatusIndicator` handles reconnecting state

**Verification:** 185 tests, 82.28% coverage, all quality gates green (ruff, mypy, tsc, vitest).

---

## Phase 9: Molecule Visualization Suite (Feb 10) -- DONE

Full visualization: server-side 2D SVG depiction, 3Dmol.js for 3D/docking views, expandable candidate detail panel.

### 9A. Server-Side 2D Depiction
- [x] `RDKitAdapter.depict_2d(smiles, width, height)` -- RDKit `rdMolDraw2D.MolDraw2DSVG`
- [x] `ChemistryService.depict_2d()` thin wrapper
- [x] Tests: returns SVG, custom dimensions, invalid SMILES raises (3 tests)

### 9B. Molecule API Routes
- [x] `GET /molecule/depict?smiles=&w=&h=` -- SVG response, 24h cache, error SVG for invalid SMILES
- [x] `GET /molecule/conformer?smiles=` -- JSON with mol_block, energy, num_atoms
- [x] `GET /molecule/descriptors?smiles=` -- JSON descriptors + passes_lipinski
- [x] `GET /targets` -- JSON list of protein targets (5 pre-configured)
- [x] Router registered in app.py
- [x] Tests: 10 API tests (depict, conformer, descriptors, targets)

### 9C. 3Dmol.js Integration
- [x] Added `3dmol` package to console dependencies
- [x] TypeScript type stubs (`console/src/types/3dmol.d.ts`)
- [x] Dynamic import for code splitting (~575KB separate chunk)

### 9D. Molecule Viewer Components
- [x] `MolViewer2D`: `<img>` tag with server-side SVG, lazy loading, error fallback to SMILES text
- [x] `MolViewer3D`: 3Dmol.js WebGL viewer, stick style, Jmol coloring, cleanup on unmount
- [x] `DockingViewer`: 3Dmol.js protein cartoon (spectrum) + ligand stick (green carbon), zoom to ligand
- [x] Tests: 4 MolViewer2D component tests (src, encoding, dimensions, error fallback)

### 9E. CandidateDetail + CandidateTable
- [x] `CandidateDetail` panel: parallel fetch of conformer + descriptors, 3-column grid (2D | 3D + energy | properties + Lipinski badge)
- [x] `CandidateTable` rewrite: 2D thumbnails (80x60), chevron expand/collapse, click-to-expand detail panel
- [x] Removed raw SMILES column (SMILES in img alt text)
- [x] Updated tests for new table structure

### 9F. Cleanup
- [x] Deleted `useRDKit` hook (dead code)
- [x] Added `CandidateDetail` to barrel export (`index.ts`)

**Verification:** 198 tests, 82.09% coverage, 19 console tests. All quality gates green (ruff 0, mypy 0, tsc 0, vitest 19/19).

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
     Phase 5 (Agent Loop) -- DONE
           |
     Phase 6 (Console) -- DONE
           |
     Phase 7 (Integration + Demo) -- DONE
           |
     Phase 8 (Multi-Model + Polish) -- DONE
           |
     Phase 9 (Molecule Visualization) -- DONE
           |
     Phase 10A (Hypothesis-Driven Engine) -- DONE
           |
     Scientific Methodology Upgrade (cross-cutting) -- All 6 Phases DONE
           |
     Domain-Agnostic Generalization -- DONE
           |
     Multi-Domain Investigations -- DONE
           |
     Self-Referential Research -- DONE
           |
     Demo + Video -- TODO
           |
     Submission (Feb 16, 3PM ET) -- TODO
```

## Scientific Methodology Upgrade (Cross-Cutting)

Grounding every phase of the investigation workflow in established scientific methodology. Each phase gets the treatment that Phase 1 (Hypothesis) received: deep research, universal components, entity upgrades, prompt updates. See [`docs/scientific-methodology.md`](scientific-methodology.md) for full details.

| # | Phase | Status |
|---|-------|--------|
| 1 | Hypothesis Formulation (Popper, Platt, Feynman, Bayesian) | DONE |
| 2 | Literature Survey (PICO, citation chasing, GRADE, AMSTAR-2) | DONE |
| 3 | Experiment Design (Fisher, controls, sensitivity, AD) | DONE |
| 4 | Evidence Evaluation (evidence hierarchy, GRADE, effect sizes) | DONE |
| 5 | Negative Controls (Z'-factor, permutation significance, scaffold-split) | DONE |
| 6 | Synthesis (GRADE certainty, priority tiers, knowledge gaps) | DONE |

---

## Phase 10A: Hypothesis-Driven Investigation Engine (Feb 10) -- DONE

Replaced the linear 7-phase pipeline with a hypothesis-driven scientific method loop.

### Architecture Change
- **Old:** Literature -> Data -> Model -> Screen -> Structure -> Resistance -> Conclude (linear recipe)
- **New:** Literature Survey -> Formulate Hypotheses -> For each: Design Experiment -> Execute -> Evaluate -> Negative Controls -> Synthesize

### Domain Layer
- [x] `Hypothesis` entity: statement, rationale, status (proposed/testing/supported/refuted/revised), confidence, evidence lists
- [x] `Experiment` entity: hypothesis_id, description, tool_plan, status, result_summary
- [x] `NegativeControl` frozen dataclass: identifier, identifier_type, score, threshold, correctly_classified property (generalized in Domain-Agnostic phase)
- [x] `Finding` modified: `hypothesis_id` + `evidence_type` replace `phase`
- [x] `Investigation` modified: hypotheses, experiments, negative_controls replace phases

### Events (12 total, was 11)
- [x] Removed: `PhaseStarted`, `PhaseCompleted`, `DirectorPlanning`, `DirectorDecision`
- [x] Added: `HypothesisFormulated`, `ExperimentStarted`, `ExperimentCompleted`, `HypothesisEvaluated`, `NegativeControlRecorded`
- [x] Modified: `FindingRecorded` (hypothesis_id + evidence_type), `InvestigationCompleted` (hypotheses + negative_controls)

### Tools (23 total, was 19)
- [x] 4 new control tools: `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_negative_control`
- [x] Modified: `record_finding` (hypothesis_id + evidence_type), `conclude_investigation` (hypothesis assessments)

### Orchestrators
- [x] Single-model `Orchestrator`: hypothesis control tool dispatch with entity creation
- [x] `MultiModelOrchestrator`: hypothesis-driven loop (formulate -> design -> execute -> evaluate per hypothesis)
- [x] 7 hypothesis-driven prompts replacing 6 phase-based prompts

### Console
- [x] `HypothesisBoard` + `HypothesisCard`: kanban-style status grid with confidence bars
- [x] `ActiveExperimentCard`: replaces `ActivePhaseCard` with experiment context
- [x] `NegativeControlPanel`: validation table with pass/fail indicators
- [x] `FindingsPanel`: evidence type badges + hypothesis grouping
- [x] `Timeline`: hypothesis/experiment/evaluation event rendering
- [x] Deleted: `PhaseProgress.tsx`, `ActivePhaseCard.tsx`

### Persistence
- [x] SQLite schema: hypotheses, experiments, negative_controls columns (JSON serialized)
- [x] Removed: phases, current_phase columns

**Verification:** 212 tests passed, mypy 0 errors, ruff 0 violations, tsc 0 errors, bun build success.

---

## Domain-Agnostic Generalization (Feb 11-12) -- DONE

Generalized the entire engine from molecular-science-specific to domain-agnostic. Proved the architecture works by adding Sports Science as a second domain.

### Backend Entity Generalization
- [x] `Candidate` entity: generic `identifier`/`identifier_type`/`scores`/`attributes` (replaces `smiles`/`prediction_score`/`docking_score`/`admet_score`/`resistance_risk`)
- [x] `NegativeControl` entity: generic `identifier`/`identifier_type`/`score`/`threshold` (replaces `smiles`/`prediction_score`)
- [x] `NegativeControlRecorded` event: generic fields
- [x] SQLite serialization updated for new field names
- [x] All 274 existing tests pass after entity changes

### Domain Configuration + Tool Tagging
- [x] `DomainConfig` + `ScoreDefinition` frozen dataclasses
- [x] `DomainRegistry`: register, detect by classified category, list template prompts
- [x] `MOLECULAR_SCIENCE` config (6 tool tags, 3 scores, 4 templates, multishot examples)
- [x] `SPORTS_SCIENCE` config (2 tool tags, 3 scores, 2 templates, multishot examples)
- [x] `ToolRegistry` with domain tag filtering (`list_schemas_for_domain`, `list_tools_for_domain`)
- [x] Tools tagged: chemistry, analysis, prediction, simulation, sports, literature; investigation control universal
- [x] `DomainDetected` SSE event (16th event type) sends display config to frontend

### Prompt Template Generalization
- [x] Builder functions: `build_scientist_prompt()`, `build_formulation_prompt()`, `build_experiment_prompt()`, `build_synthesis_prompt()`
- [x] Dynamic domain classification from all registered domain categories
- [x] HypothesisType enum expanded: PHYSIOLOGICAL, PERFORMANCE, EPIDEMIOLOGICAL

### Frontend Generalization
- [x] Dynamic score columns from `DomainDisplayConfig` (replaces hardcoded Pred/Dock/ADMET/Resist)
- [x] Conditional MolViewer2D: only when `identifier_type === "smiles"`
- [x] Conditional Lab View tab: only when `visualization_type === "molecular"`
- [x] 6 template cards (4 molecular + 2 sports) with domain badges
- [x] Generic candidate comparison, negative control panel, markdown export

### Sports Science Bounded Context (6 new tools)
- [x] `search_sports_literature` -- Semantic Scholar with sports context
- [x] `analyze_training_evidence` -- effect sizes, heterogeneity, evidence grading (A-D)
- [x] `compare_protocols` -- evidence-weighted composite scoring
- [x] `assess_injury_risk` -- knowledge-based multi-factor risk scoring
- [x] `compute_training_metrics` -- ACWR, monotony, strain, RPE load
- [x] `search_supplement_evidence` -- supplement meta-analysis search
- [x] 14 new sports tests, all passing

**Verification:** 288 server tests, 107 console tests. All quality gates green: ruff 0, mypy 0 (117 files), tsc 0, vitest 107/107.

---

## Multi-Domain Investigations (Feb 12) -- DONE

Cross-domain research questions that span multiple scientific domains (e.g., molecular + sports science).

### Changes

- [x] `DomainRegistry.detect()` returns `list[DomainConfig]` (multi-domain detection, deduplicates)
- [x] Haiku classifier outputs JSON array of domain categories
- [x] `merge_domain_configs()` creates synthetic merged config (union tool_tags, concatenated scores, joined examples)
- [x] Tool filtering uses merged config's union of domain tags
- [x] Prompt examples merged from all relevant domains
- [x] `DomainDetected` SSE event carries merged display config with `domains` sub-list
- [x] Frontend `DomainDisplayConfig.domains` for sub-domain rendering
- [x] Tests: 16 tests (multi-detect, deduplication, fallback, merge, display dict)

---

## Self-Referential Research (Feb 12) -- DONE

Ehrlich builds institutional knowledge by querying its own past investigations during new research.

### Changes

- [x] SQLite FTS5 virtual table (`findings_fts`) on finding title, detail, evidence_type, hypothesis statement/status, source provenance
- [x] `search_prior_research` tool (38th tool) -- intercepted in orchestrator, routed to FTS5 via repository
- [x] BM25-ranked full-text search with investigation prompt context
- [x] FTS5 query sanitization (quoted tokens for literal hyphens/operators)
- [x] FTS5 index rebuilt on investigation completion via `_rebuild_fts()`
- [x] Provenance: `source_type: "ehrlich"`, `source_id: "{investigation_id}"`
- [x] Available during Phase 2 (Literature Survey) alongside external search tools
- [x] Frontend: Ehrlich-branded source badges with internal navigation
- [x] Tests: 6 FTS5 tests (empty, match, prompt context, limit, completion-gating, cross-investigation)

---

## Phase 10B: Additional Organisms -- BACKLOG

Expand beyond MRSA to cover the WHO critical/high-priority pathogens.

### 10A. Organism Registry
- [ ] Centralized organism config: name, ChEMBL target IDs, protein targets, known resistance mutations
- [ ] E. coli (Gram-negative, ESBL-producing)
- [ ] P. aeruginosa (Gram-negative, carbapenem-resistant)
- [ ] A. baumannii (Gram-negative, pan-drug resistant)
- [ ] M. tuberculosis (mycobacterium, MDR/XDR-TB)

### 10B. Protein Targets per Organism
- [ ] E. coli: PBP3, DNA Gyrase, Dihydrofolate reductase (DHFR)
- [ ] P. aeruginosa: OprM efflux, PBP3, DNA Gyrase
- [ ] A. baumannii: OXA-23 beta-lactamase, PBP1a, DNA Gyrase
- [ ] M. tuberculosis: InhA (isoniazid target), KatG, DprE1

### 10C. Resistance Knowledge Base Expansion
- [ ] Per-organism mutation profiles with literature references
- [ ] Compound class patterns per organism (not just MRSA)
- [ ] Cross-organism resistance comparison

### 10D. Prompts + Agent Guidance
- [ ] Update system prompts to handle multi-organism investigations
- [ ] Organism-aware phase guidance (e.g., different screening strategies for Gram-neg vs mycobacteria)

**Verification:** All existing tests pass + new organism config tests. Agent can run investigations against any of the 5 organisms.

---

## Phase 11: Investigation Comparison -- BACKLOG

Side-by-side comparison of investigation runs for reproducibility and consensus analysis.

### 11A. Comparison Domain
- [ ] `Comparison` entity: list of investigation IDs, consensus candidates, overlap metrics
- [ ] Candidate overlap calculation (by SMILES / Tanimoto similarity threshold)
- [ ] Finding overlap detection (by phase + title similarity)
- [ ] Score aggregation across runs (mean, std, min, max)

### 11B. Comparison API
- [ ] `POST /compare` -- accept list of investigation IDs, return comparison
- [ ] `GET /compare/{id}` -- retrieve saved comparison

### 11C. Comparison Console
- [ ] `/compare` page: pick 2+ completed investigations
- [ ] Side-by-side candidate table with overlap highlighting
- [ ] Consensus candidates panel (appear in N/M runs)
- [ ] Score distribution visualization (per candidate across runs)
- [ ] Findings diff view (shared vs unique per run)

**Verification:** Compare 2 completed investigations, verify overlap metrics and consensus candidates render correctly.

---

## Phase 12: MCP Server -- BACKLOG

Expose Ehrlich as a tool server for Claude Code / Claude Desktop via Model Context Protocol.

### 12A. MCP Transport
- [ ] Stdio transport for Claude Code integration
- [ ] SSE transport for Claude Desktop / remote clients
- [ ] Tool registration: expose all 38 Ehrlich tools as MCP tools

### 12B. Investigation Tool
- [ ] `start_investigation(prompt, organism)` -- kick off full investigation, return ID
- [ ] `get_investigation(id)` -- return status, findings, candidates
- [ ] `compare_investigations(ids)` -- return comparison summary

### 12C. Documentation + Demo
- [ ] MCP server config for Claude Code (`claude_desktop_config.json`)
- [ ] Usage examples in README
- [ ] Demo: Claude Code running a full investigation via MCP

**Verification:** Claude Code can connect to Ehrlich MCP server and run an investigation end-to-end.

---

## Backlog (Post-Hackathon)

- PostgreSQL migration for production persistence
- Batch screening mode (score entire ZINC subsets)
- Antifungal/antiviral expansion
- Automated synthesis lab integration (Emerald Cloud Lab, Strateos)
- Community contributions: new tools, new targets, new models

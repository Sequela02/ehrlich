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
- [x] `to_inchikey(smiles)` -- SMILES -> InChI -> InChIKey
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

### 2B. Core Reference Set
- [x] Load `data/references/core_references.json` into `CoreReferenceSet`
- [x] Lookup by key: halicin, abaucin, who_bppl_2024, chemprop, pkcsm, amr_crisis
- [x] Expanded JSON with full metadata (key findings, training size, hit rates)
- [x] Tests: load fixture, find by key, all 6 keys verified

### 2C. Literature Service + Tools
- [x] `search_papers(query, limit)` -- Semantic Scholar
- [x] `get_reference(key)` -- core reference lookup + DOI fallback
- [x] `format_citation(paper)` -- APA-style string
- [x] Implement `search_literature` tool -- query -> JSON with papers
- [x] Implement `get_reference` tool -- key -> JSON with full citation
- [x] Tests: service with mock repos (8), tool JSON output (3)

### 2D. ChEMBL Loader
- [x] HTTP client for ChEMBL REST API (direct httpx)
- [x] Filter by: target_organism, standard_type=MIC/IC50, standard_relation="="
- [x] Deduplicate: one entry per SMILES (median activity if duplicates)
- [x] Compute pActivity: -log10(standard_value * 1e-6)
- [x] Parquet caching for downloaded datasets
- [x] Build `Dataset` entity: smiles_list, activities, metadata
- [ ] Tests: mock API (deferred -- uses mock service in tools tests)

### 2E. Analysis Service + Tools
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
- [x] Register all tools from all contexts (6 chemistry, 3 literature, 6 analysis, 3 prediction, 7 simulation, 6 training, 4 nutrition, 7 investigation control -- 38 at time of Phase 5; now 48 with API tools + visualization tools)
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
- [x] 20 event types (see README for full list): hypothesis lifecycle, experiment lifecycle, tool calls, findings, thinking, controls, validation, phases, cost, domain detection, literature survey, visualization, completion, error
- [x] Include cost tracker data in completed event
- [x] Tests: event type conversions + JSON format

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
- [x] Researcher (Sonnet) executes experiments with 48 domain-filtered tools (max 10 iterations per experiment)
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
Phase 2A-C    Phase 2D-E
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
     Shared Context + MCP Bridge + Training/Nutrition APIs -- DONE
           |
     Domain-Specific Visualization System -- DONE
           |
     Claude SDK Optimization -- DONE
           |
     Landing Site (web/) -- DONE
     (TanStack Start + SSR)
           |
     ┌─────┼──────────────┐
     │     │              │
Training  Nutrition   Competitive
Enhancement Enhancement  Sports
  (TODO)    (TODO)     Domain (TODO)
     │     │              │
     └─────┼──────────────┘
           |
     Phase 12: SaaS Infrastructure -- TODO
     (PostgreSQL + WorkOS Auth + BYOK + Credits)
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

Generalized the entire engine from molecular-science-specific to domain-agnostic. Proved the architecture works by adding Training Science and Nutrition Science as additional domains.

### Backend Entity Generalization
- [x] `Candidate` entity: generic `identifier`/`identifier_type`/`scores`/`attributes` (replaces `smiles`/`prediction_score`/`docking_score`/`admet_score`/`resistance_risk`)
- [x] `NegativeControl` entity: generic `identifier`/`identifier_type`/`score`/`threshold` (replaces `smiles`/`prediction_score`)
- [x] `NegativeControlRecorded` event: generic fields
- [x] SQLite serialization updated for new field names
- [x] All 274 existing tests pass after entity changes (274 at time of this phase)

### Domain Configuration + Tool Tagging
- [x] `DomainConfig` + `ScoreDefinition` frozen dataclasses
- [x] `DomainRegistry`: register, detect by classified category, list template prompts
- [x] `MOLECULAR_SCIENCE` config (6 tool tags, 3 scores, 4 templates, multishot examples)
- [x] `TRAINING_SCIENCE` config (3 tool tags, 3 scores, 2 templates, multishot examples)
- [x] `NUTRITION_SCIENCE` config (3 tool tags, 3 scores, 1 template, multishot examples)
- [x] `ToolRegistry` with domain tag filtering (`list_schemas_for_domain`, `list_tools_for_domain`)
- [x] Tools tagged: chemistry, analysis, prediction, simulation, training, clinical, nutrition, safety, literature; investigation control universal
- [x] `DomainDetected` SSE event (16th event type) sends display config to frontend

### Prompt Template Generalization
- [x] Builder functions: `build_scientist_prompt()`, `build_formulation_prompt()`, `build_experiment_prompt()`, `build_synthesis_prompt()`
- [x] Dynamic domain classification from all registered domain categories
- [x] HypothesisType enum expanded: PHYSIOLOGICAL, PERFORMANCE, EPIDEMIOLOGICAL

### Frontend Generalization
- [x] Dynamic score columns from `DomainDisplayConfig` (replaces hardcoded Pred/Dock/ADMET/Resist)
- [x] Conditional MolViewer2D: only when `identifier_type === "smiles"`
- [x] Unified reactive VisualizationPanel: LiveLabViewer auto-appears for molecular tool events, charts render inline
- [x] 7 template cards (4 molecular + 2 training + 1 nutrition) with domain badges
- [x] Generic candidate comparison, negative control panel, markdown export

### Training Science Bounded Context (6 tools)
- [x] `search_training_literature` -- Semantic Scholar with training science context
- [x] `analyze_training_evidence` -- effect sizes, heterogeneity, evidence grading (A-D)
- [x] `compare_protocols` -- evidence-weighted composite scoring
- [x] `assess_injury_risk` -- knowledge-based multi-factor risk scoring
- [x] `compute_training_metrics` -- ACWR, monotony, strain, RPE load
- [x] `search_clinical_trials` -- ClinicalTrials.gov exercise/training RCT search

### Nutrition Science Bounded Context (4 tools)
- [x] `search_supplement_evidence` -- supplement meta-analysis search
- [x] `search_supplement_labels` -- NIH DSLD supplement product ingredient lookup
- [x] `search_nutrient_data` -- USDA FoodData Central nutrient profiles
- [x] `search_supplement_safety` -- OpenFDA CAERS adverse event reports for supplements
- [x] Tests: training (8 tests) + nutrition (10 tests), all passing

**Verification:** 288 server tests, 107 console tests. All quality gates green: ruff 0, mypy 0 (117 files), tsc 0, vitest 107/107.

---

## Multi-Domain Investigations (Feb 12) -- DONE

Cross-domain research questions that span multiple scientific domains (e.g., molecular + nutrition, training + nutrition).

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
- [x] `search_prior_research` tool -- intercepted in orchestrator, routed to FTS5 via repository
- [x] BM25-ranked full-text search with investigation prompt context
- [x] FTS5 query sanitization (quoted tokens for literal hyphens/operators)
- [x] FTS5 index rebuilt on investigation completion via `_rebuild_fts()`
- [x] Provenance: `source_type: "ehrlich"`, `source_id: "{investigation_id}"`
- [x] Available during Phase 2 (Literature Survey) alongside external search tools
- [x] Frontend: Ehrlich-branded source badges with internal navigation
- [x] Tests: 6 FTS5 tests (empty, match, prompt context, limit, completion-gating, cross-investigation)

---

## Shared Context + MCP Bridge + Training/Nutrition APIs (Feb 12) -- DONE

DDD cleanup, shared bounded context, MCP bridge for external tools, 4 new data source clients (training + nutrition), and methodology page.

### Shared Bounded Context
- [x] `shared/` context: cross-cutting ports and value objects (`ChemistryPort` ABC, `Fingerprint`, `MolecularDescriptors`, `Conformer3D`)
- [x] `ChemistryPort` ABC decouples chemistry operations from RDKit infrastructure
- [x] Moved value objects from `chemistry/domain/` to `shared/` for cross-context use

### MCP Bridge
- [x] `MCPBridge` connects to external MCP servers (stdio/SSE/streamable_http transports)
- [x] Tools registered dynamically via `ToolRegistry.register_mcp_tools()` with domain tags
- [x] Lifecycle managed by orchestrator (connect on start, disconnect on completion)
- [x] Enabled via `EHRLICH_MCP_EXCALIDRAW=true` env var

### Data Source API Tools (4 tools across training + nutrition)
- [x] `search_clinical_trials` (training) -- ClinicalTrials.gov v2 API for exercise/training RCTs
- [x] `search_supplement_labels` (nutrition) -- NIH DSLD supplement label database
- [x] `search_nutrient_data` (nutrition) -- USDA FoodData Central nutrient profiles
- [x] `search_supplement_safety` (nutrition) -- OpenFDA CAERS adverse event reports
- [x] Full DDD: domain entities + repository ABCs + infrastructure clients in respective bounded contexts

### Methodology Page
- [x] `GET /methodology` endpoint: phases, domains, tools, data sources, models
- [x] `GET /stats` endpoint: aggregate counts
- [x] Console methodology page with phases, models, domains, tools, data sources

**Verification:** 527 server tests, 107 console tests. All quality gates green.

---

## Domain-Specific Visualization System (Feb 12) -- DONE

6 visualization tools with structured payloads, orchestrator interception, and lazy-loaded React components.

### Backend
- [x] `VisualizationPayload` frozen dataclass (viz_type, title, data, config, domain)
- [x] 6 viz tools: `render_binding_scatter`, `render_admet_radar`, `render_training_timeline`, `render_muscle_heatmap`, `render_forest_plot`, `render_evidence_matrix`
- [x] Orchestrator intercepts viz tool results via `_maybe_viz_event()`, emits `VisualizationRendered` SSE event (20th event type)

### Frontend
- [x] `VizRegistry` maps viz_type to lazy-loaded React component
- [x] `VisualizationPanel` renders multiple charts in grid layout
- [x] Recharts: scatter (compound affinities), radar (ADMET), timeline (training load + ACWR)
- [x] Visx: forest plot (meta-analysis), evidence matrix (heatmap)
- [x] Custom SVG: anatomical body diagram with muscle activation/risk heatmap
- [x] OKLCH color tokens for consistent chart theming

**Verification:** 527 server tests, 107 console tests. All quality gates green.

---

## Claude SDK Optimization -- DONE

Upgraded the Anthropic SDK integration to use all available features for better reasoning quality, lower costs, and improved UX.

### SDK-1: Fix Pricing + Cache-Aware Cost Tracking -- DONE

Fixed incorrect hardcoded pricing and added cache hit/miss token tracking for accurate cost reporting.

- [x] Fix Opus pricing: `$15/$75` -> `$5/$25` per M tokens (Opus 4.5/4.6 pricing)
- [x] Fix Haiku pricing: `$0.80/$4.0` -> `$1/$5` per M tokens (Haiku 4.5 pricing)
- [x] Track `cache_creation_input_tokens` and `cache_read_input_tokens` from `response.usage`
- [x] Compute cache-aware cost: cache writes at 1.25x, cache reads at 0.1x base input rate
- [x] Add `cache_read_tokens` and `cache_write_tokens` to `CostTracker.to_dict()`
- [x] Update `CostUpdate` SSE event with cache breakdown
- [x] Update `MessageResponse` dataclass with cache token fields
- [x] Tests: cost calculation with cache hits, cache misses, mixed scenarios

**Files:** `cost_tracker.py`, `anthropic_client.py`, `multi_orchestrator.py`, `events.py`, `sse.py`, `test_cost_tracker.py`

### SDK-2: Prompt Caching on Tools Array -- DONE

Cache the 48-tool schema array that repeats on every researcher API call.

- [x] Add `cache_control: {"type": "ephemeral"}` to the last tool in the tools array before passing to `messages.create`
- [x] Only apply when tools list is non-empty
- [x] No changes to tool registry -- caching applied at the adapter level

**Files:** `anthropic_client.py`

### SDK-3: Effort Parameter -- DONE

Use `effort` to control token spend per model role.

- [x] Add `effort: str | None = None` parameter to `AnthropicClientAdapter.__init__`
- [x] Pass `effort` to `messages.create()` when set (omit when None for backward compat)
- [x] Configure per-model in `Settings`:
  - Director (Opus 4.6): `effort="high"` (default, explicit)
  - Researcher (Sonnet 4.5): `effort="high"` (default, explicit)
  - Summarizer (Haiku 4.5): `effort="low"` (simple compression tasks)
- [x] Add `EHRLICH_DIRECTOR_EFFORT`, `EHRLICH_RESEARCHER_EFFORT`, `EHRLICH_SUMMARIZER_EFFORT` env vars
- [x] Wire in API route when creating adapters

**Files:** `config.py`, `anthropic_client.py`, `routes/investigation.py`

### SDK-4: Extended Thinking for Director -- DONE

Enabled extended thinking on Opus 4.6 Director for deeper scientific reasoning.

- [x] Add `thinking: dict | None = None` parameter to `AnthropicClientAdapter.__init__`
- [x] Pass `thinking` to `messages.create()` when set
- [x] Default for Director: `{"type": "enabled", "budget_tokens": 10000}`
- [x] Parse `thinking` content blocks in `_parse_content_blocks()` -- extract `block.thinking` text
- [x] Emit thinking text via existing `Thinking` SSE event (already supported in frontend)
- [x] `max_tokens` increased to 32768 for Director to accommodate thinking budget
- [x] Add `EHRLICH_DIRECTOR_THINKING` env var (enabled/disabled)
- [x] Track thinking tokens separately in `MessageResponse` (thinking tokens billed as output)

**Files:** `config.py`, `anthropic_client.py`, `multi_orchestrator.py`, `routes/investigation.py`

### SDK-5: Structured Outputs for Director (Medium Impact) -- DONE

Guarantee valid JSON from Director calls (hypothesis formulation, experiment design, evaluation, synthesis).

- [x] Add `output_config: dict | None = None` parameter to `AnthropicClientAdapter.create_message()` and `stream_message()`
- [x] Pass `output_config` to `messages.create()` / `messages.stream()` when set
- [x] Define JSON schemas for Director outputs (6 schemas in `domain/schemas.py`):
  - `PICO_SCHEMA` -- PICO decomposition for literature survey
  - `FORMULATION_SCHEMA` -- array of hypothesis objects
  - `EXPERIMENT_DESIGN_SCHEMA` -- experiment plan object
  - `EVALUATION_SCHEMA` -- evaluation result object
  - `SYNTHESIS_SCHEMA` -- synthesis result object
  - `LITERATURE_GRADING_SCHEMA` -- evidence grading result
- [x] Update Director call sites in `MultiModelOrchestrator` to pass schemas via `_build_output_config()`
- [x] Remove `_parse_json()` fallback -- structured outputs guarantee valid JSON
- [x] Structured outputs work alongside streaming (`stream_message` with `output_config`)

**Files:** `anthropic_client.py`, `multi_orchestrator.py`, `investigation/domain/schemas.py` (new)

### SDK-6: tool_choice Control -- DONE

Control how the researcher uses tools.

- [x] Add `tool_choice: dict | None = None` parameter to `AnthropicClientAdapter.create_message()`
- [x] Pass `tool_choice` to `messages.create()` when set
- [x] Researcher first turn: `tool_choice={"type": "any"}` to force tool use (researcher should always start by calling tools)
- [x] Researcher subsequent turns: `tool_choice=None` (default, let model decide)
- [x] Literature survey first turn: `tool_choice={"type": "any"}` to force tool use

**Files:** `anthropic_client.py`, `multi_orchestrator.py`

### SDK-7: Streaming API (High Impact, UX) -- DONE (Director only)

Replace non-streaming `messages.create()` with streaming for real-time Director token display.

- [x] Add `stream_message()` async generator method to `AnthropicClientAdapter`
- [x] Use `client.messages.stream()` (high-level SDK helper) for async context manager
- [x] Yield intermediate events: `thinking` and `text` deltas, plus `result` with final `MessageResponse`
- [x] Accumulate final message via `stream.get_final_message()` for usage tracking
- [x] Update `MultiModelOrchestrator._director_call()` to use streaming -- yields `Thinking` events in real time
- [x] Emit real-time `Thinking` events as thinking tokens stream in (no buffering)
- [x] Keep non-streaming `create_message()` for Researcher and Summarizer (tool dispatch loop is simpler without streaming)
- [x] Retry with exponential backoff on `RateLimitError` / `APITimeoutError` (same as `create_message`)

**Files:** `anthropic_client.py`, `multi_orchestrator.py`

### Implementation Summary

SDK-1 through SDK-7 all implemented. SDK-1 through SDK-4 and SDK-6 done in parallel by 3 agents (`sdk-cost`, `sdk-adapter`, `sdk-wiring`). SDK-5 (Structured Outputs) and SDK-7 (Director Streaming) wired in subsequently.

### Verification

**Completed:** 540 server tests passing, 107 console tests passing. All quality gates green.

- `uv run pytest` -- 540 passed (13 new tests for SDK features)
- `uv run ruff check src/ tests/` -- zero violations
- `uv run mypy src/ehrlich/` -- zero errors (140 source files)
- `bun run build && bun run typecheck` -- zero errors
- `bunx vitest run` -- 107 passed

---

## Landing Site (`web/`) -- DONE

Separate TanStack Start project for the public-facing landing page. SSR/SSG for SEO, same React + TypeScript + Bun stack as console, independent build and deployment.

### Why Separate from Console

- **Different concerns**: landing page is marketing/SEO content; console is the authenticated SPA
- **Different optimization**: SSR/SSG with zero-JS static pages vs client-side SPA with heavy WebGL/charting
- **Independent deployment**: CDN-friendly static output vs API-connected app server
- **Clean separation**: no marketing code in the investigation UI, no app dependencies in the landing page

### Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | TanStack Start | Same TanStack ecosystem as console, SSR/SSG built-in, Nitro server |
| Runtime | Bun | Same as console |
| Styling | Tailwind CSS 4 | Same as console, shared design tokens (OKLCH) |
| Fonts | Space Grotesk + JetBrains Mono | Same as console (Lab Protocol identity) |
| Icons | Lucide React | Same as console |
| Build | Vite 7 (via Nitro) | Same toolchain |

### Project Structure

```
web/
├── src/
│   ├── routes/
│   │   ├── __root.tsx            # Root layout (shell, SEO meta, font loading)
│   │   └── index.tsx             # Landing page (all sections wired)
│   ├── components/
│   │   ├── Nav.tsx               # Fixed navbar with scroll progress bar + mobile menu
│   │   ├── Footer.tsx            # Minimal footer (links, license, year)
│   │   ├── SectionHeader.tsx     # Mono label with left border accent
│   │   ├── Hero.tsx              # Bottom-third hero with ASCII bg, stats bar, CTAs
│   │   ├── Architecture.tsx      # Director-Worker-Summarizer diagram with connectors
│   │   ├── Methodology.tsx       # 6-phase pipeline with glow-pulse active node
│   │   ├── Domains.tsx           # 3 asymmetric domain cards with tool counts
│   │   ├── DataSources.tsx       # 13 sources with large number visual anchor
│   │   ├── OpenSource.tsx        # Typography-driven sparse section
│   │   └── CTA.tsx               # Minimal CTA with arrow links
│   ├── styles/
│   │   └── app.css               # Tailwind 4 entry + OKLCH tokens + animations
│   ├── lib/
│   │   ├── constants.ts          # Stats, links, domain data, methodology phases
│   │   ├── ascii-patterns.ts     # ASCII art backgrounds (hero, arch, methodology, data)
│   │   ├── use-reveal.ts         # IntersectionObserver scroll reveal hook
│   │   └── use-scroll-progress.ts # Scroll progress fraction hook
│   ├── router.tsx                # TanStack Router factory (getRouter)
│   └── routeTree.gen.ts          # Auto-generated route tree
├── public/
│   └── favicon.svg               # Green "E" favicon
├── package.json                  # ehrlich-web, Bun scripts
├── vite.config.ts                # TanStack Start + Nitro + Tailwind
└── tsconfig.json                 # src/ paths, strict mode
```

### WEB-1: Project Scaffolding -- DONE

- [x] TanStack Start project in `web/` with Bun
- [x] `vite.config.ts` with tanstackStart + nitro + tailwindcss + viteReact + tsConfigPaths
- [x] Tailwind CSS 4 with OKLCH design tokens matching console's Lab Protocol identity
- [x] Space Grotesk + JetBrains Mono font loading via Google Fonts
- [x] Root layout with `shellComponent`, `HeadContent`, CSS `?url` import
- [x] Favicon + meta tags (title, description, OG, Twitter card, theme-color)
- [x] `bun run build` produces `.output/` (client + SSR + Nitro server)
- [x] `bun run typecheck` -- zero errors

### WEB-2: Landing Page Sections -- DONE

- [x] **Hero**: bottom-third placement, ASCII background, stats bar (48 tools, 13 sources, 3 domains, 3 models), CTA buttons
- [x] **Architecture**: Director-Worker-Summarizer diagram with fork/merge connectors, color-coded accent bars, stagger-children animation
- [x] **Methodology**: 6-phase pipeline with connecting line, glow-pulse on active node (Hypothesis Formulation), theoretical basis block
- [x] **Domains**: 3 asymmetric grid cards (5/4/3 col spans), tool count badges, capabilities, sources, example prompts
- [x] **DataSources**: large "13" visual anchor left, 2-column source list right, conditional access badges
- [x] **OpenSource**: typography-driven sparse section (py-32), 3-column feature grid, GitHub link
- [x] **CTA**: 3 arrow links (Launch Console, Self-Host with Docker, Read the Docs)

### WEB-3: Navigation + Footer + Meta -- DONE

- [x] **Nav**: fixed top bar, scroll progress indicator, desktop links, mobile hamburger menu
- [x] **Footer**: AGPL-3.0 branding, mapped footer links, responsive layout
- [x] **SectionHeader**: mono label with left border accent (reused across sections)
- [x] **SEO meta**: full OG tags, Twitter card, theme-color, description
- [x] **Smooth scroll**: anchor links (`#architecture`, `#methodology`, `#domains`, `#data-sources`)
- [x] Responsive: mobile hamburger nav, stacked sections

### WEB-5: Visual Polish + Animations -- DONE

- [x] Scroll-triggered section reveals via `useReveal` (IntersectionObserver, one-shot)
- [x] Staggered children animation (80ms delay cascade, CSS-only)
- [x] Phase pipeline glow-pulse on active node
- [x] Domain cards hover effects (-translate-y-[1px], border-primary)
- [x] Architecture cards stagger-children animation
- [x] ASCII art backgrounds at 3% opacity (hero, architecture, methodology, data sources)
- [x] Scroll progress bar in navbar
- [x] All OKLCH tokens (zero hardcoded gray-* classes)

### Verification

- [x] `cd web && bun run build` -- zero errors
- [x] `cd web && bun run typecheck` -- zero TypeScript errors
- [x] Visual: Lab Protocol identity consistent with console (OKLCH tokens, fonts, dark theme)
- [x] All docs updated: `CLAUDE.md`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`

---

## Training Science Enhancement -- TODO

Deepen the training bounded context with more data sources and richer analytical capabilities.

### New Data Sources
- [ ] PubMed API (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`) -- exercise physiology literature (better biomedical coverage than Semantic Scholar alone for RCTs and clinical studies)
- [ ] Exercise database -- muscle groups, movement patterns, biomechanics reference data (Wger API or curated YAML)

### New Tools
- [ ] `search_pubmed_training` -- PubMed E-utilities search for exercise/training papers (MeSH terms, structured abstracts)
- [ ] `search_exercise_database` -- exercise lookup by muscle group, movement pattern, equipment

### Improvements
- [ ] PubMed integration in literature survey (alongside Semantic Scholar for broader coverage)
- [ ] Richer injury risk model (integrate epidemiological data from PubMed systematic reviews)
- [ ] Periodization analysis tool (macro/meso/micro cycle planning based on evidence)

---

## Nutrition Science Enhancement -- TODO

Deepen the nutrition bounded context with analytical tools, visualization, and interaction screening.

### New Tools
- [ ] `compare_nutrients` -- side-by-side nutrient comparison between 2+ foods or supplements (macros, micros, amino acid profiles)
- [ ] `analyze_dose_response` -- dose-response modeling from literature data (optimal dose ranges, diminishing returns)
- [ ] `check_interactions` -- supplement-drug and supplement-supplement interaction screening (contraindications, synergies)

### New Visualization
- [ ] `render_nutrient_comparison` -- bar/radar chart comparing nutrient profiles across foods/supplements (Recharts)

### New Data Sources
- [ ] PubMed API -- nutrition and supplement research (shared with training context via literature bounded context)
- [ ] Drug interaction database (DrugBank open data or OpenFDA drug labels) for interaction checking

### Improvements
- [ ] RDA/DRI reference data (WHO/USDA recommended daily allowances) for context in nutrient comparisons
- [ ] Bioavailability annotations on nutrient data (e.g., heme vs non-heme iron absorption rates)

---

## Competitive Sports Domain -- TODO

New bounded context for actual competitive sports analytics: game statistics, player performance, team analysis, and sports-specific strategy research.

### Bounded Context: `sports/`

```
server/src/ehrlich/sports/
├── domain/
│   ├── entities.py          # Player, Team, GameStats, SeasonStats, PerformanceMetric
│   └── repository.py        # SportsDataRepository ABC
├── application/
│   └── sports_service.py    # SportsService (stats analysis, performance comparison)
├── infrastructure/
│   └── *_client.py          # API clients for sports data providers
└── tools.py                 # Tools for Claude
```

### Data Sources (Research Needed)
- [ ] Basketball: NBA API / Basketball Reference (player stats, advanced metrics, play-by-play)
- [ ] Soccer/Football: football-data.org or API-Football (match results, player stats, league standings)
- [ ] American Football: NFL data feeds (player stats, play-by-play, combine data)
- [ ] General: ESPN API or Sports Reference family (multi-sport coverage)

### Planned Tools
- [ ] `search_player_stats` -- player statistics by name/team/season (points, assists, rebounds, goals, etc.)
- [ ] `compare_players` -- side-by-side player comparison with advanced metrics
- [ ] `analyze_team_performance` -- team-level analytics (win rate, offensive/defensive efficiency)
- [ ] `search_sports_literature` -- Semantic Scholar + PubMed for sports-specific research (tactics, biomechanics, game theory)
- [ ] `compute_advanced_metrics` -- sport-specific advanced stats (PER, WAR, xG, passer rating, etc.)
- [ ] `analyze_matchup` -- head-to-head matchup analysis between players or teams

### Domain Config: `COMPETITIVE_SPORTS`
- tool_tags: `{"sports", "literature"}`
- valid_domain_categories: `("competitive_sports", "basketball", "soccer", "football", "baseball", "tennis")`
- hypothesis_types: `("performance", "tactical", "statistical", "predictive")`
- score_definitions: performance_score, statistical_significance, sample_size
- identifier_type: `"player"` or `"team"`

### Visualization
- [ ] `render_player_radar` -- radar chart comparing player attributes (Recharts)
- [ ] `render_season_timeline` -- performance trends over a season (Recharts)
- [ ] `render_shot_chart` -- spatial shot/play visualization (Custom SVG, basketball/soccer)

### Cross-Domain Potential
- Sports + Training: "What training protocols produce the best NBA pre-season conditioning results?"
- Sports + Nutrition: "What supplements do elite soccer players use and what's the evidence?"
- Sports + Molecular: "What are the pharmacological mechanisms behind caffeine's effect on sprint performance?"

---

## Additional Domains -- BACKLOG

The engine is domain-agnostic via `DomainConfig` + `DomainRegistry`. Adding a new domain requires zero changes to existing code (see `CONTRIBUTING.md`). Potential future domains:

- [ ] Genomics / bioinformatics (variant interpretation, gene expression analysis)
- [ ] Environmental science (pollutant fate, ecosystem modeling)
- [ ] Materials science (property prediction, synthesis planning)
- [ ] Clinical pharmacology (drug interactions, pharmacokinetics)

For molecular science specifically:
- [ ] Expanded organism coverage (E. coli, P. aeruginosa, A. baumannii, M. tuberculosis)
- [ ] Per-organism resistance knowledge base with literature references
- [ ] Organism-aware prompt guidance (Gram-neg vs mycobacteria screening strategies)

---

## Phase 11: Investigation Comparison -- BACKLOG

Side-by-side comparison of investigation runs for reproducibility and consensus analysis.

### 11A. Comparison Domain
- [ ] `Comparison` entity: list of investigation IDs, consensus candidates, overlap metrics
- [ ] Candidate overlap calculation (by identifier + domain-specific similarity)
- [ ] Finding overlap detection (by hypothesis + title similarity)
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

## MCP Server -- BACKLOG

Expose Ehrlich as an MCP tool server for Claude Code / Claude Desktop.

> **Note:** Ehrlich already has an MCP **client** bridge (`investigation/infrastructure/mcp_bridge.py`) that connects TO external MCP servers (e.g., Excalidraw for visual summaries). This backlog item is the reverse: exposing Ehrlich's 48 tools as an MCP server.

- [ ] Stdio + SSE transports for Claude Code / Claude Desktop
- [ ] Tool registration: expose all 48 Ehrlich tools as MCP tools
- [ ] `start_investigation(prompt)` -- kick off investigation, return ID
- [ ] `get_investigation(id)` -- return status, findings, candidates
- [ ] MCP server config for Claude Code (`claude_desktop_config.json`)
- [ ] Demo: Claude Code running an investigation via MCP

---

## Phase 12: SaaS Infrastructure -- TODO

Production deployment with authentication, API key management, and usage tracking.

### 12A. PostgreSQL Migration

Replace SQLite with PostgreSQL for production persistence.

- [ ] `PostgresInvestigationRepository` implementing existing `InvestigationRepository` ABC
- [ ] `asyncpg` connection pooling (replace `aiosqlite`)
- [ ] FTS5 to PostgreSQL `tsvector` + GIN index (self-referential research)
- [ ] `JSONB` columns for hypotheses, experiments, findings, candidates
- [ ] `users` table: id, email, credits, encrypted_api_key, created_at
- [ ] `DATABASE_URL` env var (replaces `EHRLICH_DB_PATH`)
- [ ] Migration script (SQLite data export -> PostgreSQL import)
- [ ] Tests with testcontainers-postgresql

### 12B. Authentication (WorkOS AuthKit)

User identity via WorkOS (1M MAU free tier). JWT-based, provider-swappable.

- [ ] WorkOS dashboard setup (Google social login, redirect URIs)
- [ ] Frontend: `@workos-inc/authkit-react` provider + `<AuthKitProvider>`
- [ ] Backend: JWT verification middleware on protected routes
- [ ] `user_id` extraction from JWT, linked to `users` table
- [ ] Public routes: `GET /health`, `GET /methodology`, `GET /stats`
- [ ] Protected routes: `POST /investigate`, `GET /investigate/{id}/stream`, BYOK endpoints
- [ ] Env vars: `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`

### 12C. BYOK (Bring Your Own Key)

Users provide their own Anthropic API key. Key never persisted in plaintext.

- [ ] Frontend: API key input in settings, stored in `localStorage`
- [ ] `X-Anthropic-Key` header sent per SSE connection
- [ ] Backend: use provided key for that investigation, fall back to platform key
- [ ] Key validation endpoint (`POST /validate-key`)
- [ ] BYOK users bypass credit system -- pay Anthropic directly

### 12D. Credit System

Usage-based credits tracked per user. Free tier on signup, BYOK unlimited.

- [ ] `credits` column on `users` table (default: 5 free on signup)
- [ ] Credit deduction on investigation completion (mapped from `CostTracker` actual cost)
- [ ] `GET /user/credits` -- current balance
- [ ] Frontend: credit badge in header, exhaustion prompt (BYOK or wait)
- [ ] Credit tiers: Free (5), BYOK (unlimited), future paid packs
- [ ] Credit-to-dollar conversion rate configurable (e.g., 1 credit = $0.25)

### 12E. Cost Transparency (PostHog Model)

Radical cost transparency -- since the codebase is open source (AGPL-3.0), hiding costs would be disingenuous. Users can see the `_MODEL_PRICING` dict in the source code anyway. Instead, use cost visibility as a differentiator.

**Industry context:** 79/500 SaaS companies use credit models (up 126% YoY). 65% of IT leaders report surprise AI charges. PostHog openly shows their 20% markup on LLM costs.

**Dual-mode cost display (adapts to user's billing mode):**

| Mode | Primary Display | Expandable Detail |
|------|----------------|-------------------|
| BYOK | `$0.47 API cost` (user's money, billed by Anthropic) | Token breakdown by model, cache savings |
| Credits | `2 credits used` (platform billing unit) | Token breakdown, equivalent API cost, cache savings |

**Implementation:**

- [ ] `CostBreakdown` component: primary metric + expandable detail panel
- [ ] Primary metric adapts to billing mode (credits vs BYOK dollar cost)
- [ ] Expandable detail always shows: tokens (input/output/cache read/cache write) by model (Director/Researcher/Summarizer), cache savings estimate, total API cost
- [ ] Cache savings highlight: "Saved $X.XX via prompt caching" -- validates the SDK optimization work (SDK-1, SDK-2)
- [ ] `CostTracker` feeds both modes: `total_cost` for BYOK display, `total_cost` -> credit conversion for credit display
- [ ] Cost data available in investigation detail page (completed investigations) and real-time during SSE stream
- [ ] No cost obfuscation -- raw API cost always accessible in expandable detail regardless of billing mode

**Files:** `console/src/features/investigation/components/CostBreakdown.tsx`, update `InvestigationReport.tsx`, update SSE event handling for cache-aware cost data

### 12F. Deployment

- [ ] Docker multi-stage build (Python backend)
- [ ] PostgreSQL instance (managed or containerized)
- [ ] Frontend: Vercel (static Vite build)
- [ ] DNS: backend API + frontend app
- [ ] Secrets management via environment variables
- [ ] SSL via Let's Encrypt / platform provider
- [ ] Backup schedule for PostgreSQL

**Verification:** Full E2E: sign in with Google -> start investigation -> credits deducted -> cost breakdown shows credits + token detail -> BYOK key input -> investigation uses user key -> cost breakdown shows dollar cost + token detail -> credits unchanged.

---

## Backlog (Post-Hackathon)

- Batch screening mode (score entire ZINC subsets)
- Automated synthesis lab integration (Emerald Cloud Lab, Strateos)
- Community contributions: new domains, new tools, new data sources
- Rewarded ads for free credits (AdMob/AdSense integration)
- Stripe integration for paid credit packs
- Admin dashboard for usage analytics

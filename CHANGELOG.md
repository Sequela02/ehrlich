# Changelog

All notable changes to Ehrlich will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Molecule visualization: server-side 2D SVG depiction via RDKit `rdMolDraw2D` (`depict_2d` on RDKitAdapter and ChemistryService)
- Molecule API: `GET /molecule/depict` returns `image/svg+xml` with 24h cache, error SVG for invalid SMILES
- Molecule API: `GET /molecule/conformer` returns 3D conformer JSON (mol_block, energy, num_atoms)
- Molecule API: `GET /molecule/descriptors` returns molecular descriptors + Lipinski pass/fail
- Molecule API: `GET /targets` returns list of protein targets (pdb_id, name, organism)
- Console: `MolViewer2D` component -- server-side SVG via `<img>` tag with lazy loading and error fallback
- Console: `MolViewer3D` component -- 3Dmol.js WebGL viewer with stick style and Jmol coloring
- Console: `DockingViewer` component -- 3Dmol.js protein (cartoon/spectrum) + ligand (stick/green) overlay
- Console: `CandidateDetail` expandable panel with 2D/3D views, property card, and Lipinski badge
- Console: `CandidateTable` rewrite with 2D structure thumbnails, expand/collapse rows, chevron indicators
- Console: 3Dmol.js dependency for 3D molecular visualization
- Tests: 10 molecule API tests, 3 RDKit depict tests, 4 MolViewer2D component tests

### Removed

- Console: `useRDKit` hook (dead code, replaced by server-side SVG rendering)

### Changed

- `CandidateTable` replaces raw SMILES text column with inline 2D structure thumbnails (80x60)
- `CandidateTable` rows are now clickable to expand `CandidateDetail` panel

---

### Added

- Multi-model: Director-Worker-Summarizer architecture (Opus 4.6 plans, Sonnet 4.5 executes tools, Haiku 4.5 compresses large outputs)
- Multi-model: `MultiModelOrchestrator` with phase-based execution, director review, and final synthesis
- Multi-model: Per-model cost tracking with tiered pricing (Opus $15/$75, Sonnet $3/$15, Haiku $0.80/$4 per M tokens)
- Multi-model: 5 new prompts -- director planning, review, synthesis, researcher phase, summarizer
- Multi-model: 3 new domain events -- `DirectorPlanning`, `DirectorDecision`, `OutputSummarized`
- Multi-model: 3 new SSE event types -- `director_planning`, `director_decision`, `output_summarized`
- Persistence: SQLite repository with WAL mode via `aiosqlite` for investigation storage
- Persistence: `InvestigationRepository` ABC in domain layer
- API: `GET /investigate` -- list all investigations (most recent first)
- API: `GET /investigate/{id}` -- full investigation detail with findings, candidates, cost
- API: Automatic orchestrator selection (multi-model when researcher != director, single-model fallback)
- Console: SSE reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- Console: Investigation history list on home page with status badges and candidate counts
- Console: Phase progress bar (7-segment) with active/completed/inactive states
- Console: Director event rendering in Timeline (planning, decision, output summarized)
- Console: `useInvestigations` hook with TanStack Query (10s refetch interval)
- Investigation: `created_at` and `cost_data` fields on Investigation entity
- Config: Per-model settings (`EHRLICH_DIRECTOR_MODEL`, `EHRLICH_RESEARCHER_MODEL`, `EHRLICH_SUMMARIZER_MODEL`)
- Config: `EHRLICH_SUMMARIZER_THRESHOLD`, `EHRLICH_MAX_ITERATIONS_PER_PHASE`, `EHRLICH_DB_PATH`
- Tests: 25+ new tests for multi-model orchestrator, SQLite repository, updated API and cost tracker

### Fixed

- Added `pyarrow` to core dependencies -- required for ChEMBL parquet caching (`explore_dataset` crashed without it)

### Changed

- Cost tracker refactored to track per-model usage with model-specific pricing breakdown
- `AnthropicClientAdapter` exposes `model` property for cost attribution
- Orchestrator passes model to `cost.add_usage()` for accurate per-model tracking
- API routes use SQLite repository instead of in-memory dict
- `InvestigationCompleted` event includes `candidates` list
- SSE `completed` event includes candidates and cost data from investigation
- Integration: API key wired from `Settings` to `AnthropicClientAdapter` constructor
- Integration: Exponential backoff retry (3 attempts) for rate-limit and timeout errors
- Integration: Startup lifespan event with API key validation, tool count logging, optional dependency checks
- Integration: Data preparation script (`data/scripts/prepare_data.py`) using `ChEMBLLoader` for pre-downloading ChEMBL bioactivity data and PDB protein structures
- Integration: E2E smoke test exercising full pipeline (tool registry, orchestrator dispatch, SSE events)
- Integration: Environment variable documentation in README
- Integration: Demo instructions in README

### Changed

- Removed `modify_molecule` stub from tool registry (19 tools, down from 20)
- Improved error handling in `explore_dataset` (ChEMBL timeout, empty datasets)
- Improved error handling in `train_model` (dataset too small)
- Improved error handling in `predict_candidates` (model not found)
- Improved error handling in `dock_against_target` (invalid target, lists available targets)
- Improved error handling in `assess_resistance` (invalid target, invalid SMILES)
- Added `has_api_key` property to `Settings` for startup validation

### Fixed

- `AnthropicClientAdapter` no longer ignores `Settings.anthropic_api_key` (was reading only from env)

---

- Initial project scaffolding with DDD architecture (6 bounded contexts)
- Server: Python 3.12 + FastAPI + uv with full domain/application/infrastructure layers
- Console: React 19 + TypeScript 5.7 + Bun + Vite 6 + TanStack Router
- Shared kernel: SMILES/InChIKey/MolBlock types, Molecule value object, exception hierarchy
- API layer: FastAPI factory with CORS, health endpoint, investigation route stub
- SSE event types for real-time investigation streaming
- Investigation feature: Timeline, PromptInput, CandidateTable, ReportViewer, CostBadge
- Molecule feature: MolViewer2D, MolViewer3D, DockingViewer, PropertyCard stubs
- CI/CD: GitHub Actions (server: ruff + mypy + pytest, console: build + typecheck + test)
- Docker: multi-stage builds for server (uv + python:3.12-slim) and console (bun + nginx)
- Data: core references JSON, data preparation script, protein directory
- Optional dependency groups: `docking` (vina, meeko), `deeplearning` (chemprop)
- Pre-commit hooks: ruff lint + format
- Chemistry context: full RDKit adapter (descriptors, fingerprints, conformers, scaffolds, Butina clustering, substructure matching), ChemistryService, 7 tools (44 tests)
- Literature context: Semantic Scholar client, PubMed stub, core reference set with 6 key papers, LiteratureService, 2 tools (11 tests)
- Analysis context: ChEMBL loader with parquet caching, Tox21 loader, substructure enrichment (chi-squared), property distributions, AnalysisService, 3 tools (12 tests)
- Prediction context: XGBoost adapter (train/predict with scale_pos_weight, AUROC/AUPRC/F1 metrics, feature importance), model store (joblib save/load/list), Chemprop adapter (guarded), scaffold split, Butina clustering, ensemble, PredictionService, 3 tools (20 tests)
- Simulation context: protein store (5 MRSA targets -- PBP2a, DHPS, DNA Gyrase, MurA, NDM-1), Vina adapter (guarded), RDKit-based ADMET prediction (Lipinski, mutagenic SMARTS alerts, hERG, BBB, hepatotoxicity), knowledge-based resistance assessment (7 mutations across 5 targets, compound class pattern matching), SimulationService, 3 tools (20 tests)

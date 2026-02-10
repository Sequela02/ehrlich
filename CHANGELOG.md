# Changelog

All notable changes to Ehrlich will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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

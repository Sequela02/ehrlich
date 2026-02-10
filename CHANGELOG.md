# Changelog

All notable changes to Ehrlich will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

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

Back to [Roadmap Index](README.md)

# Phase 0: Infrastructure (Feb 10) -- DONE

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

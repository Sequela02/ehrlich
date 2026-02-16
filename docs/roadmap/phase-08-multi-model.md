Back to [Roadmap Index](README.md)

# Phase 8: Multi-Model Architecture + Polish (Feb 10) -- DONE

Cost-efficient multi-model orchestration, persistence, and UI polish.

## 8A. Domain Foundation + Config
- [x] Domain events: `OutputSummarized` (kept), hypothesis/experiment events (added in Phase 10A)
- [x] `created_at` and `cost_data` fields on Investigation entity
- [x] Per-model config settings: director, researcher, summarizer models
- [x] `summarizer_threshold`, `max_iterations_per_experiment`, `db_path` settings

## 8B. Multi-Model Cost Tracker
- [x] Per-model usage tracking with model-specific pricing
- [x] Pricing dict: Opus $15/$75, Sonnet $3/$15, Haiku $0.80/$4 per M tokens
- [x] `to_dict()` with `by_model` breakdown (director/researcher/summarizer tiers)
- [x] `AnthropicClientAdapter.model` property for cost attribution

## 8C. Multi-Model Orchestrator
- [x] `MultiModelOrchestrator` with hypothesis-driven Director-Worker-Summarizer pattern
- [x] Director (Opus) formulates hypotheses, designs experiments, evaluates evidence, synthesizes -- NO tool access
- [x] Researcher (Sonnet) executes experiments with 73 domain-filtered tools (max 10 iterations per experiment)
- [x] Summarizer (Haiku) compresses large outputs exceeding threshold
- [x] 7 prompts: director formulation/experiment/evaluation/synthesis, researcher experiment, scientist, summarizer
- [x] Auto-fallback to single-model Orchestrator when researcher == director
- [x] Tests: 12 tests across 8 classes (formulation, execution, evaluation, negative controls, compression, synthesis, full flow, errors)

## 8D. SQLite Persistence
- [x] `InvestigationRepository` ABC in domain layer
- [x] `SqliteInvestigationRepository` with WAL mode via `aiosqlite`
- [x] Single `investigations` table with JSON serialization for complex fields
- [x] Tests: 8 tests (save, retrieve, list, update, cost data)

## 8E. API Wiring
- [x] `GET /investigate` -- list all investigations (most recent first)
- [x] `GET /investigate/{id}` -- full investigation detail
- [x] SQLite repository initialization in app lifespan
- [x] Automatic orchestrator selection (multi-model vs single-model)
- [x] SSE event types: `hypothesis_formulated`, `experiment_started`, `experiment_completed`, `hypothesis_evaluated`, `negative_control`, `output_summarized`
- [x] `completed` event includes candidates and cost data

## 8F. SSE Reconnection
- [x] Exponential backoff (1s, 2s, 4s) with max 3 retries
- [x] `reconnecting` state with amber WiFi-off indicator
- [x] Reset attempt counter on successful reconnect
- [x] Track `experiments`, `hypotheses`, `negativeControls` and `toolCallCount` from events

## 8G. Investigation History
- [x] `useInvestigations` hook with TanStack Query (10s refetch)
- [x] `InvestigationList` component with status badges and candidate counts
- [x] History section on home page below prompt input

## 8H. UI Feedback
- [x] `HypothesisBoard` kanban-style grid with status columns and confidence bars
- [x] Hypothesis/experiment event rendering in Timeline
- [x] Candidates wired to `CandidateTable` from SSE completed event
- [x] `StatusIndicator` handles reconnecting state

**Verification:** 185 tests, 82.28% coverage, all quality gates green (ruff, mypy, tsc, vitest).

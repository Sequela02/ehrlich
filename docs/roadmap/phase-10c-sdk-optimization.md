Back to [Roadmap Index](README.md)

# Phase 10C: Claude SDK Optimization -- DONE

Upgraded the Anthropic SDK integration to use all available features for better reasoning quality, lower costs, and improved UX.

## SDK-1: Fix Pricing + Cache-Aware Cost Tracking -- DONE

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

## SDK-2: Prompt Caching on Tools Array -- DONE

Cache the 73-tool schema array that repeats on every researcher API call.

- [x] Add `cache_control: {"type": "ephemeral"}` to the last tool in the tools array before passing to `messages.create`
- [x] Only apply when tools list is non-empty
- [x] No changes to tool registry -- caching applied at the adapter level

**Files:** `anthropic_client.py`

## SDK-3: Effort Parameter -- DONE

Use `effort` to control token spend. Only supported by Opus models (4.5+); Sonnet and Haiku do not support it.

- [x] Add `effort: str | None = None` parameter to `AnthropicClientAdapter.__init__`
- [x] Pass `effort` via `output_config` dict to `messages.create()` (SDK 0.79+ requires it nested, not top-level)
- [x] Configure Director effort in `Settings`: `effort="high"` (default), gated on Opus model name
- [x] Add `EHRLICH_DIRECTOR_EFFORT` env var (only applied when Director model contains "opus")
- [x] Researcher (Sonnet) and Summarizer (Haiku) never receive effort -- unsupported by those models
- [x] Wire in API route when creating adapters

**Files:** `config.py`, `anthropic_client.py`, `routes/investigation.py`

## SDK-4: Extended Thinking for Director -- DONE

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

## SDK-5: Structured Outputs for Director (Medium Impact) -- DONE

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

## SDK-6: tool_choice Control -- DONE

Control how the researcher uses tools.

- [x] Add `tool_choice: dict | None = None` parameter to `AnthropicClientAdapter.create_message()`
- [x] Pass `tool_choice` to `messages.create()` when set
- [x] Researcher first turn: `tool_choice={"type": "any"}` to force tool use (researcher should always start by calling tools)
- [x] Researcher subsequent turns: `tool_choice=None` (default, let model decide)
- [x] Literature survey first turn: `tool_choice={"type": "any"}` to force tool use

**Files:** `anthropic_client.py`, `multi_orchestrator.py`

## SDK-7: Streaming API (High Impact, UX) -- DONE (Director only)

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

## Implementation Summary

SDK-1 through SDK-7 all implemented. SDK-1 through SDK-4 and SDK-6 done in parallel by 3 agents (`sdk-cost`, `sdk-adapter`, `sdk-wiring`). SDK-5 (Structured Outputs) and SDK-7 (Director Streaming) wired in subsequently.

## Verification

**Completed:** 540 server tests passing, 107 console tests passing. All quality gates green.

- `uv run pytest` -- 540 passed (13 new tests for SDK features)
- `uv run ruff check src/ tests/` -- zero violations
- `uv run mypy src/ehrlich/` -- zero errors (140 source files)
- `bun run build && bun run typecheck` -- zero errors
- `bunx vitest run` -- 107 passed

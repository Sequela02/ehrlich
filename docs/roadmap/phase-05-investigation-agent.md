Back to [Roadmap Index](README.md)

# Phase 5: Investigation Agent (Feb 10) -- DONE

The core: Claude as an autonomous scientist.

## 5A. Anthropic Client Adapter
- [x] Wrap `anthropic.AsyncAnthropic().messages.create()` -- isolate SDK dependency
- [x] Handle: system prompt, messages array, tools list, max_tokens
- [x] Parse response: content blocks (text, tool_use), stop_reason, usage
- [x] Error handling: rate limits, API errors, timeout
- [x] Tests: mock API, verify request/response handling

## 5B. Tool Registry
- [x] Register all tools from all contexts (6 chemistry, 3 literature, 12 analysis, 3 prediction, 7 simulation, 11 training, 10 nutrition, 7 investigation control -- 38 at time of Phase 5; now 79 with API tools + visualization tools + statistics tools + generic ML tools + impact tools + causal tools)
- [x] Auto-generate JSON Schema from Python type hints + docstrings
- [x] `get(name)` -> callable, `list_tools()` -> all registered tools, `list_schemas()` -> Anthropic-compatible schemas
- [x] Schema format matches Anthropic tool_use specification
- [x] Tests: register tool, verify schema generation, lookup, list params, defaults (8 tests)

## 5C. Cost Tracker
- [x] Track per-run: input_tokens, output_tokens, tool_calls count
- [x] Compute cost: Sonnet 4.5 pricing ($3/M input, $15/M output)
- [x] Running totals across iterations, `to_dict()` for serialization
- [x] Tests: add_usage, verify total_cost calculation (6 tests)

## 5D. System Prompt
- [x] Scientist persona: Paul Ehrlich, methodology, phases, rules
- [x] 7 research phases with specific tool guidance per phase
- [x] Constraints: minimum 3 tools per phase, always cite references, record findings
- [x] Output format: structured findings + ranked candidates + citations

## 5E. Orchestrator -- Agentic Loop
- [x] Create `Investigation` entity, set status to RUNNING
- [x] Build messages array: system prompt + user research question
- [x] Loop: call Claude -> check stop_reason -> dispatch tool_use -> collect results -> repeat
- [x] Max iteration guard (configurable, default 50)
- [x] Emit domain events: HypothesisFormulated, ExperimentStarted, ExperimentCompleted, HypothesisEvaluated, NegativeControlRecorded, ToolCalled, ToolResultEvent, FindingRecorded, Thinking, InvestigationCompleted, InvestigationError
- [x] Handle: parallel tool calls (Claude can request multiple), tool errors (graceful JSON error return)
- [x] End condition: stop_reason == "end_turn", conclude_investigation called, or max iterations
- [x] Phase auto-detection from tool names
- [x] Tests: mock Claude responses with tool_use, verify dispatch + event emission (9 tests)

## 5F. SSE Streaming
- [x] Convert domain events to SSE events via `domain_event_to_sse()` mapper
- [x] Wire orchestrator async generator to `sse-starlette` EventSourceResponse
- [x] 20 event types (see README for full list): hypothesis lifecycle, experiment lifecycle, tool calls, findings, thinking, controls, validation, phases, cost, domain detection, literature survey, visualization, completion, error
- [x] Include cost tracker data in completed event
- [x] Tests: event type conversions + JSON format

## 5G. Investigation API Routes
- [x] `POST /api/v1/investigate` -- accept prompt, create investigation, return ID
- [x] `GET /api/v1/investigate/{id}/stream` -- SSE stream of orchestrator events
- [x] Request/response DTOs with Pydantic models (InvestigateRequest, InvestigateResponse)
- [x] Error handling: 404 invalid ID, 409 investigation already running
- [x] Tests: FastAPI TestClient (4 tests)

## 5H. Control Tools
- [x] `record_finding(title, detail, hypothesis_id, evidence_type)` -- orchestrator intercepts and stores in Investigation entity
- [x] `conclude_investigation(summary, candidates, citations)` -- orchestrator intercepts, sets candidates/citations, ends loop
- [x] `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_negative_control` -- hypothesis control tools
- [x] Tests: verify finding storage, conclusion structure, hypothesis tools (10 tests)

**Verification:** `uv run pytest tests/investigation/ tests/api/ -v` -- 41 passed. Full suite 153 passed, 82% coverage, ruff 0, mypy 0.

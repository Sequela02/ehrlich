Back to [Roadmap Index](README.md)

# Phase 6: Console Integration (Feb 10) -- DONE

Visualization and real-time streaming UI.

## 6A. ~~RDKit.js WASM Integration~~ (Replaced by server-side SVG)
- [x] Replaced with server-side RDKit `rdMolDraw2D` SVG depiction (higher quality, simpler)
- [x] Deleted `useRDKit` hook (dead code)

## 6B. Molecule Viewers
- [x] `MolViewer2D`: server-side SVG via `<img src="/api/v1/molecule/depict">`, lazy loading, error fallback
- [x] `MolViewer3D`: 3Dmol.js WebGL viewer with stick style, Jmol coloring, dynamic import
- [x] `DockingViewer`: 3Dmol.js protein cartoon (spectrum) + ligand stick (green carbon) overlay
- [x] `PropertyCard`: display descriptors with generic property grid

## 6C. Investigation Flow
- [x] Wire `PromptInput` to `useInvestigation` mutation (POST /investigate)
- [x] Navigate to `/investigation/$id` on success
- [x] `useSSE` hook: named event listeners for all 7 SSE event types, parsed state (currentPhase, findings, summary, cost, error)
- [x] `Timeline`: rich rendering per event type with phase icons, tool call previews, finding highlights
- [x] `FindingsPanel`: sidebar panel showing accumulated findings with phase badges
- [x] `CandidateTable`: populate from conclusion event data
- [x] `ReportViewer`: render markdown summary from conclude event
- [x] `CostBadge`: live token/cost from SSE completed event

## 6D. Polish
- [x] Loading states: spinner on connecting, "Starting..." on submit
- [x] Error states: connection lost, API errors, inline error messages
- [x] Responsive layout: 3-column grid on desktop (timeline + report | findings + candidates)
- [x] Status indicator: connecting / running (animated) / completed / error
- [x] Auto-scroll timeline to latest event
- [x] Tests: component rendering with mock data (14 tests across 4 files)

**Verification:** `npx vitest run` -- 19 passed. `bun run build` + `tsc --noEmit` -- zero errors.

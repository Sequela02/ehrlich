Back to [Roadmap Index](README.md)

# Phase 12: Platform Infrastructure (Feb 13) -- DONE

The COSS managed-hosting layer: production-ready authentication, credit-based billing, model-tiered investigations, and PostgreSQL persistence for the hosted instance.

> Business rationale and pricing research: see [business-strategy.md](../adr/business-strategy.md)

## 12A. PostgreSQL Migration -- DONE

Replaced SQLite with PostgreSQL for multi-tenant persistence.

- [x] `InvestigationRepository` implementing existing `InvestigationRepository` ABC
- [x] `asyncpg` connection pooling (replaced `aiosqlite`)
- [x] `tsvector` + GIN index for self-referential research (replaces FTS5)
- [x] `JSONB` columns for hypotheses, experiments, findings, candidates
- [x] `users` table: id (UUID), workos_id, email, credits, encrypted_api_key, created_at
- [x] `credit_transactions` table: user_id, amount, type, investigation_id, created_at
- [x] `EHRLICH_DATABASE_URL` env var (replaces `EHRLICH_DB_PATH`)
- [x] `sqlite_repository.py` deleted, `aiosqlite` removed from dependencies

## 12B. Authentication (WorkOS AuthKit) -- DONE

User identity via WorkOS (1M MAU free tier). JWT-based.

- [x] `api/auth.py` with JWKS verification via `PyJWKClient`
- [x] Frontend: `@workos-inc/authkit-react` provider + `<AuthKitProvider>`
- [x] Backend: `get_current_user`, `get_current_user_sse`, `get_optional_user` dependencies
- [x] `user_id` extraction from JWT, linked to `users` table via `get_or_create_user()`
- [x] Public routes: `GET /health`, `GET /methodology`, `GET /stats`, `GET /molecule/*`, `GET /investigate/{id}`
- [x] Protected routes: `POST /investigate`, `GET /investigate`, `GET /investigate/{id}/stream`, `POST /investigate/{id}/approve`, `GET /credits/balance`
- [x] Env vars: `EHRLICH_WORKOS_API_KEY`, `EHRLICH_WORKOS_CLIENT_ID`
- [x] SSE auth via `?token=` query param fallback (EventSource does not support headers)

## 12C. Universal Credit System -- DONE

One currency. User decides model quality per investigation.

- [x] Credit spending: Haiku Director = 1 credit, Sonnet Director = 3 credits, Opus Director = 5 credits
- [x] Researcher always Sonnet 4.5, Summarizer always Haiku 4.5 (regardless of tier)
- [x] `GET /credits/balance` -- current balance + BYOK status
- [x] `POST /investigate` accepts `director_tier: "haiku" | "sonnet" | "opus"` parameter
- [x] Credit deduction on investigation start (not completion -- prevents abuse)
- [x] Credit refund on investigation failure
- [x] Default 5 credits for new users

## 12D. BYOK (Bring Your Own Key) -- DONE

Users provide their own Anthropic API key. Bypasses credit system.

- [x] Frontend: `BYOKSettings.tsx` for API key management, stored in `localStorage`
- [x] `X-Anthropic-Key` header sent with requests
- [x] Backend: `api_key_override` forwarded to `AnthropicClientAdapter`
- [x] BYOK users bypass credit system -- pay Anthropic directly

## 12E. Cost Transparency -- DONE

Users see exactly what each investigation costs.

- [x] `CompletionSummaryCard` with expandable cost breakdown
- [x] Tokens (input/output/cache read/cache write) by model role (Director/Researcher/Summarizer)
- [x] Cost data in real-time during SSE stream via `CostUpdate` events

## 12F-H. Deferred to Post-Hackathon

- [ ] Ad-funded bonus credits (12F)
- [ ] AGPL dual licensing docs (12G)
- [ ] Production deployment (12H)

**Verification:** Auth flow, credit deduction/refund, BYOK pass-through, tier selection, cost breakdown all working.

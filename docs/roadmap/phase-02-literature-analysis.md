Back to [Roadmap Index](README.md)

# Phase 2: Literature + Analysis (Feb 10) -- DONE

> **Evolution note:** This phase established the literature search and bioactivity analysis foundation. Originally chemistry-specific (ChEMBL, Semantic Scholar), the analysis tools were later generalized into domain-agnostic components in [Phase 10B](phase-10b-domain-agnostic.md).

Two independent contexts. Can be built in parallel.

## 2A. Semantic Scholar Client
- [x] HTTP client with `httpx` -- search endpoint (`/graph/v1/paper/search`)
- [x] Parse response: title, authors, year, abstract, DOI, citationCount
- [x] Rate limiting: respect 100 req/sec unauthenticated limit
- [x] Error handling: timeout, 429 rate limit, malformed response
- [x] Tests: Paper entity construction from API response (3 tests)

## 2B. Core Reference Set
- [x] Load `data/references/core_references.json` into `CoreReferenceSet`
- [x] Lookup by key: halicin, abaucin, who_bppl_2024, chemprop, pkcsm, amr_crisis
- [x] Expanded JSON with full metadata (key findings, training size, hit rates)
- [x] Tests: load fixture, find by key, all 6 keys verified

## 2C. Literature Service + Tools
- [x] `search_papers(query, limit)` -- Semantic Scholar
- [x] `get_reference(key)` -- core reference lookup + DOI fallback
- [x] `format_citation(paper)` -- APA-style string
- [x] Implement `search_literature` tool -- query -> JSON with papers
- [x] Implement `get_reference` tool -- key -> JSON with full citation
- [x] Tests: service with mock repos (8), tool JSON output (3)

## 2D. ChEMBL Loader
- [x] HTTP client for ChEMBL REST API (direct httpx)
- [x] Filter by: target_organism, standard_type=MIC/IC50, standard_relation="="
- [x] Deduplicate: one entry per SMILES (median activity if duplicates)
- [x] Compute pActivity: -log10(standard_value * 1e-6)
- [x] Parquet caching for downloaded datasets
- [x] Build `Dataset` entity: smiles_list, activities, metadata
- [ ] Tests: mock API (deferred -- uses mock service in tools tests)

## 2E. Analysis Service + Tools
- [x] `explore(target, threshold)` -- load dataset, return stats
- [x] `analyze_substructures(dataset)` -- chi-squared enrichment on 10 known substructures
- [x] `compute_properties(dataset)` -- descriptor distributions (active vs inactive)
- [x] Implement `explore_dataset` tool -- target -> JSON with stats
- [x] Implement `analyze_substructures` tool -- target -> JSON with enriched substructures
- [x] Implement `compute_properties` tool -- target -> JSON with property distributions
- [x] Tests: mock datasets (6), enrichment logic, property computation, tool output (3)

**Verification:** `uv run pytest tests/literature/ tests/analysis/ -v` -- 23 passed.

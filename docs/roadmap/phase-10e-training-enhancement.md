Back to [Roadmap Index](README.md)

# Phase 10E: Training Science Enhancement (Feb 12) -- DONE

Deepened the training bounded context with 2 new data sources, 4 new tools, and 3 new visualization tools.

## New Data Sources
- [x] PubMed API (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`) -- exercise physiology literature via E-utilities (ESearch + EFetch)
- [x] wger API (`https://wger.de/api/v2`) -- exercise database with muscles, equipment, categories

## New Tools
- [x] `search_pubmed_training` -- PubMed E-utilities search for exercise/training papers (MeSH terms, structured abstracts)
- [x] `search_exercise_database` -- exercise lookup by muscle group, movement pattern, equipment
- [x] `compute_performance_model` -- Banister fitness-fatigue model (CTL/ATL/TSB via EWMA)
- [x] `compute_dose_response` -- dose-response curve from dose-effect data points

## New Visualization Tools
- [x] `render_performance_chart` -- Recharts ComposedChart with fitness/fatigue/performance curves
- [x] `render_funnel_plot` -- Visx scatter plot for publication bias detection
- [x] `render_dose_response` -- Visx area+line chart for dose-response curves

## Infrastructure
- [x] `PubMedRepository` ABC + `PubMedClient` adapter (ESearch JSON + EFetch XML parsing)
- [x] `ExerciseRepository` ABC + `WgerClient` adapter (REST with pagination)
- [x] 4 new domain entities: `PubMedArticle`, `Exercise`, `PerformanceModelPoint`, `DoseResponsePoint`
- [x] Frontend: 3 lazy-loaded chart components registered in `VizRegistry`

## Phase 2 (Deferred Items -- Now Complete)
- [x] PubMed integration in literature survey (domain-specific prompt guidance + search stats tracking)
- [x] Richer injury risk model (epidemiological context from PubMed systematic reviews)
- [x] `plan_periodization` tool (linear/undulating/block models with evidence-based prescriptions)
- [x] 2 new domain entities: `PeriodizationBlock`, `PeriodizationPlan`
- [x] `SEARCH_TOOLS` module-level frozenset for search stats tracking

**Counts:** 48 → 56 tools, 13 → 15 data sources, 6 → 9 viz tools. 577 server tests, 107 console tests.

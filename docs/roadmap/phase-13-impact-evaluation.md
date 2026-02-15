Back to [Roadmap Index](README.md)

# Phase 13: Impact Evaluation Domain -- DONE

New bounded context for hypothesis-driven causal analysis of social programs. Domain-agnostic methodology works for any program type (sports, health, education, employment, housing) in any country. Initial focus: Mexico and US. Causal inference methods (DiD, PSM, RDD, Synthetic Control) live in `analysis/` as domain-agnostic tools usable by any domain. No existing platform combines autonomous hypothesis formulation, automated causal inference, public API integration, and evidence-graded reporting. See `docs/adr/impact-evaluation-domain.md` for full design.

## Market Gap

Of 2,800 evaluations commissioned by CONEVAL in Mexico, only 11 are impact evaluations (0.4%). No competitor combines: autonomous hypothesis formulation + causal inference + public API connectors + evidence grading + multi-model orchestration.

## Phase 13A: Foundation (Universal APIs + Domain Config) -- DONE

- [x] World Bank API client (`https://api.worldbank.org/v2/`) -- development indicators by country
- [x] WHO GHO API client (`https://ghoapi.azureedge.net/api/`) -- health statistics
- [x] FRED API client (`https://api.stlouisfed.org/fred/`) -- 800K+ economic time series
- [x] `search_economic_indicators` tool -- query FRED/World Bank/WHO GHO time series
- [x] `fetch_benchmark` tool -- get comparison values from international sources
- [x] `compare_programs` tool -- cross-program comparison using existing statistical tests
- [x] `IMPACT_EVALUATION` domain config with detection keywords and experiment examples
- [x] Full DDD: domain entities + repository ABCs + infrastructure clients
- [x] Tests: impact bounded context (unit + integration)

**Counts:** 70 -> 73 tools, 16 -> 19 data sources (18 external + 1 internal), 10 -> 11 bounded contexts, 3 -> 4 domains.

## Phase 13B (partial): Causal Inference + Impact Viz -- DONE

- [x] `CausalEstimator` port ABC in `impact/domain/ports.py` (initial placement)
- [x] `DiDEstimator` infrastructure with parallel trends test and automated threat assessment
- [x] `estimate_did` tool -- difference-in-differences with effect size, SE, p-value, threats, evidence tier
- [x] `assess_threats` tool -- knowledge-based validity threat assessment (DiD, PSM, RDD, RCT, IV)
- [x] `render_program_dashboard` viz tool -- multi-indicator KPI dashboard with target tracking
- [x] `render_geographic_comparison` viz tool -- region bar chart with benchmark reference line
- [x] `render_parallel_trends` viz tool -- DiD treatment vs control over time
- [x] Console: 3 new React chart components (ProgramDashboard, GeographicComparison, ParallelTrends)
- [x] Console: 2 Impact Evaluation template cards (CCT School Enrollment, Health Worker Programs)
- [x] Tests: DiD estimator + tool tests (35+ new tests)

**Counts:** 73 -> 78 tools, 12 -> 15 viz tools, 3 -> 5 impact tools.

## Phase 13B: Domain-Agnostic Causal Inference -- DONE

Refactored causal inference from impact-specific to domain-agnostic. All causal estimation methods now live in `analysis/` (alongside statistics), usable by any domain.

- [x] Moved `ThreatToValidity`, `CausalEstimate` entities from `impact/domain/` to `analysis/domain/causal.py`
- [x] Moved `evaluation_standards.py` (WWC tiers, CONEVAL, CREMAA) from `impact/domain/` to `analysis/domain/evidence_standards.py`
- [x] Created `analysis/domain/causal_ports.py` -- 4 estimator port ABCs: `DiDEstimatorPort`, `PSMEstimatorPort`, `RDDEstimatorPort`, `SyntheticControlPort`
- [x] Moved `DiDEstimator` from `impact/infrastructure/` to `analysis/infrastructure/did_estimator.py`
- [x] New `analysis/infrastructure/psm_estimator.py` -- propensity score matching with balance diagnostics
- [x] New `analysis/infrastructure/rdd_estimator.py` -- regression discontinuity (sharp/fuzzy)
- [x] New `analysis/infrastructure/synthetic_control_estimator.py` -- synthetic control method
- [x] New `analysis/application/causal_service.py` -- orchestrates all 4 estimators + threat assessment + cost-effectiveness
- [x] New `compute_cost_effectiveness` tool -- cost per unit outcome, ICER
- [x] Deleted `impact/domain/ports.py` -- causal estimator port moved to analysis/
- [x] Trimmed `ImpactService` -- removed DiD/threat methods (delegated to CausalService)
- [x] Impact tools reduced from 5 to 3 (estimate_did + assess_threats moved to analysis/)
- [x] 6 causal tools tagged `"causal"` in analysis/tools.py
- [x] New `render_rdd_plot` viz tool -- regression discontinuity scatter with cutoff (Visx)
- [x] New `render_causal_diagram` viz tool -- DAG showing treatment/outcome/confounders (Visx)
- [x] Console: `RDDPlot.tsx`, `CausalDiagram.tsx` chart components
- [x] Console: `ThreatAssessment.tsx` panel with severity badges
- [x] Console: 2 new template cards (Education Policy, Health Policy) -- 9 total
- [x] VizRegistry updated with 2 new viz types

**Counts:** 78 -> 84 tools (6 causal + 1 cost-effectiveness - 2 moved + 2 viz), 15 -> 17 viz tools, 5 -> 3 impact tools, 0 -> 6 causal tools (analysis/), 7 -> 9 templates.

## Phase 13A-2: Document Upload -- DONE

- [x] File upload API (`POST /upload`) with multipart/form-data, 50MB limit, WorkOS auth
- [x] PDF text extraction (`pymupdf`) with page-level parsing and 8000-char truncation
- [x] CSV/Excel parsing (`pandas` + `openpyxl`) with summary statistics and sample rows
- [x] `UploadedFile` domain entity with `TabularData` / `DocumentData` frozen dataclasses
- [x] `FileProcessor` application service (zero external deps in domain layer)
- [x] PostgreSQL `uploaded_files` table with JSONB `parsed_data` column
- [x] Inject uploaded data into Director/Researcher prompts as `<uploaded_data>` XML block
- [x] `query_uploaded_data` tool -- intercepted by `ToolDispatcher`, pandas-based filtering (eq/gt/lt/gte/lte/contains)
- [x] Upload-first flow: `POST /upload` returns preview, `POST /investigate` references `file_ids`
- [x] Frontend: `FileUpload.tsx` drag-and-drop component with progress spinner
- [x] Frontend: `DataPreview.tsx` compact inline cards for tabular/document previews
- [x] Frontend: `use-upload.ts` TanStack Query mutation hook
- [x] Tests: 16 server tests (FileProcessor + domain entities + query handler) + 16 console tests

**Counts:** 84 -> 85 tools (added `query_uploaded_data`). Investigation tools: 7 -> 8.

## Phase 13C: Mexico Integration -- DONE

- [x] INEGI Indicadores API client (`https://www.inegi.org.mx/app/api/indicadores/`) -- economic/demographic time series
- [x] Banxico SIE client (`https://www.banxico.org.mx/SieAPIRest/service/v1/`) -- central bank financial series
- [x] datos.gob.mx CKAN client (`https://datos.gob.mx/busca/api/3/action/`) -- 1000+ federal open datasets
- [x] `search_economic_indicators` extended with `source="inegi"` and `source="banxico"` branches
- [x] `search_open_data` extended with `source="datosgob"` branch for datos.gob.mx
- [x] `analyze_program_indicators` tool -- MIR logical framework indicator analysis with all 6 CREMAA criteria
- [x] Mexico domain categories added: `mexico_social_program`, `coneval_evaluation`
- [x] 2 Mexico template prompts (CONEVAL program evaluation, Banxico monetary policy)
- [x] Mexico tool examples in `experiment_examples` (INEGI, Banxico, datos.gob.mx, CREMAA)
- [x] `ImpactService`: `search_inegi_data`, `search_banxico_data`, `search_mexican_open_data`, `analyze_program_indicators`
- [x] Tests: 37 new tests (test_mx_clients.py + test_mx_tools.py)

**Counts:** 90 -> 91 tools (+1 `analyze_program_indicators`), 25 -> 27 data sources (+INEGI, Banxico, datos.gob.mx). Note: data.gov was already counted separately.

Deferred (post-hackathon): INEGI DENUE, Transparencia Presupuestaria, `extract_mir`, `MIRTable.tsx`, CONEVAL ECR report template.

## Phase 13D: US Integration -- DONE

- [x] Census Bureau API client (`https://api.census.gov/data/`) -- ACS 5-year demographics, poverty, education
- [x] BLS API client (`https://api.bls.gov/publicAPI/v2/`) -- employment, wages, CPI time series
- [x] USAspending API client (`https://api.usaspending.gov/api/v2/`) -- federal grants/contracts search
- [x] College Scorecard API client (`https://api.data.gov/ed/collegescorecard/v1/`) -- education outcomes
- [x] HUD API client (`https://www.huduser.gov/hudapi/public/`) -- Fair Market Rents, income limits
- [x] CDC WONDER client (`https://wonder.cdc.gov/`) -- mortality/natality via XML API
- [x] data.gov CKAN client (`https://catalog.data.gov/api/3/action/`) -- federal dataset discovery
- [x] `search_health_indicators` tool -- routes to WHO GHO or CDC WONDER by source
- [x] `search_spending_data` tool -- USAspending awards/grants search
- [x] `search_education_data` tool -- College Scorecard school outcomes
- [x] `search_housing_data` tool -- HUD FMR and income limits
- [x] `search_open_data` tool -- data.gov CKAN dataset metadata
- [x] Extended `search_economic_indicators` with BLS and Census sources
- [x] WWC evidence tier classification (already in `analysis/domain/evidence_standards.py`)
- [x] US-focused domain config: 6 template prompts, expanded detection keywords, experiment examples

**Counts:** 85 -> 90 tools (+5 new), 19 -> 25 data sources (+6: Census, BLS, USAspending, College Scorecard, HUD, CDC WONDER). Also added data.gov client (shares tool with datos.gob.mx).

## Data Sources (13 implemented)

| Source | API | Purpose | Auth | Phase | Status |
|--------|-----|---------|------|-------|--------|
| World Bank | `https://api.worldbank.org/v2/` | Development indicators by country | None | 13A | DONE |
| WHO GHO | `https://ghoapi.azureedge.net/api/` | Health statistics by country | None | 13A | DONE |
| FRED | `https://api.stlouisfed.org/fred/` | 800K+ economic time series | API key | 13A | DONE |
| US Census Bureau | `https://api.census.gov/data/` | ACS 5-year demographics | API key (optional) | 13D | DONE |
| BLS | `https://api.bls.gov/publicAPI/v2/` | Employment, wages, CPI | API key | 13D | DONE |
| USAspending | `https://api.usaspending.gov/api/v2/` | Federal grants, contracts | None | 13D | DONE |
| College Scorecard | `https://api.data.gov/ed/collegescorecard/v1/` | Education outcomes | API key | 13D | DONE |
| HUD | `https://www.huduser.gov/hudapi/public/` | Housing data (FMR, income limits) | Bearer token | 13D | DONE |
| CDC WONDER | `https://wonder.cdc.gov/` | Mortality, natality (XML API) | None | 13D | DONE |
| data.gov | `https://catalog.data.gov/api/3/action/` | Federal dataset discovery (CKAN) | None | 13D | DONE |
| INEGI Indicadores | `https://www.inegi.org.mx/app/api/indicadores/` | Mexico economic/demographic time series | Token | 13C | DONE |
| Banxico SIE | `https://www.banxico.org.mx/SieAPIRest/service/v1/` | Mexico central bank financial series | Token | 13C | DONE |
| datos.gob.mx | `https://datos.gob.mx/busca/api/3/action/` | Mexico open data (CKAN, 1000+ datasets) | None | 13C | DONE |
| INEGI DENUE | `https://www.inegi.org.mx/app/api/denue/v1/` | Mexico business directory (5M+) | Token | 13C | DEFERRED |
| Transparencia Presupuestaria | `https://nptp.hacienda.gob.mx/` | Mexico budget execution | None | 13C | DEFERRED |

## Tools (Planned: ~18 new tools + ~6 viz tools)

**Data Access:** `search_census_data`, `search_economic_indicators`, `search_budget_data`, `search_health_indicators`, `search_open_data`, `fetch_benchmark`
**Causal Inference:** `estimate_did`, `estimate_psm`, `estimate_rdd`, `estimate_synthetic_control`, `assess_threats`
**Program Analysis:** `analyze_program_indicators`, `compute_cost_effectiveness`, `compare_programs`, `analyze_beneficiary_data`
**Document Processing:** `extract_program_data`, `extract_mir`, `generate_evaluation_report`
**Visualization:** `render_causal_diagram`, `render_parallel_trends`, `render_rdd_plot`, `render_program_dashboard`, `render_cost_effectiveness`, `render_geographic_comparison`

# Impact Evaluation Domain -- Comprehensive Design Document

## Executive Summary

Ehrlich's **Impact Evaluation** domain enables hypothesis-driven causal analysis of social programs. Domain-agnostic methodology works for any program type (sports, health, education, employment, housing) in any country. Initial focus: Mexico and US.

**Key insight:** Of 2,800 evaluations commissioned by CONEVAL in Mexico, only 11 are impact evaluations (0.4%). No existing platform combines autonomous hypothesis formulation, automated causal inference, public API integration, and evidence-graded reporting.

---

## 1. Market Gap Analysis

### What Exists Today

| Category | Tools | Limitation |
|----------|-------|------------|
| Traditional M&E | DevResults, ActivityInfo, Bonterra, Amp Impact | Data collection + dashboards only. No causal inference. No AI. $4K-$14K/year |
| AI-enhanced M&E | Sopact Impact Cloud, DHIS2 | Pattern detection only. No causal inference. Health-specific (DHIS2) |
| General AI | ChatGPT, Julius AI, Claude | User-guided step-by-step. No autonomous hypothesis formulation. No public API connectors |
| Academic | Rayyan, LASER AI, Cochrane | Systematic reviews of published literature only. No primary program data |
| Government | CONEVAL evaluations | Manual process. 1-5 year timelines. External consultants |

### 6 Gaps No Competitor Fills

1. **Autonomous hypothesis formulation** from research questions
2. **Automated causal inference** (DiD, PSM, RDD, synthetic control)
3. **Public API integration** (INEGI, Census, World Bank, BLS)
4. **Evidence-graded reports** (GRADE framework on primary data)
5. **Multi-model orchestration** (Director-Worker-Summarizer)
6. **Real-time testing** (minutes/hours vs years)

---

## 2. Data Sources

### Tier 1 -- Built-in APIs (Universal)

| Source | API Base URL | Auth | Data | Priority |
|--------|-------------|------|------|----------|
| World Bank | `https://api.worldbank.org/v2/` | None | Development indicators, GDP, education, health by country | HIGH |
| WHO GHO | `https://ghoapi.azureedge.net/api/` | None | Health statistics by country | HIGH |
| FRED | `https://api.stlouisfed.org/fred/` | API key | 800K+ economic time series | HIGH |
| OECD | `https://sdmx.oecd.org/public/rest/` | None | Policy, education, employment indicators | MEDIUM |

### Tier 2 -- Mexico APIs

| Source | API Base URL | Auth | Data | Priority |
|--------|-------------|------|------|----------|
| INEGI Indicadores | `https://www.inegi.org.mx/app/api/indicadores/` | Token | Census, demographics, economic indicators | HIGH |
| INEGI DENUE | `https://www.inegi.org.mx/app/api/denue/v1/` | Token | 5M+ business establishments by location | MEDIUM |
| datos.gob.mx | `https://datos.gob.mx/api/3/action/` | Token (optional) | 1000+ federal datasets (CKAN) | HIGH |
| Transparencia Presupuestaria | `https://nptp.hacienda.gob.mx/apoyosdelgobierno/` | None | Budget execution, social program spending | HIGH |
| Banxico SIE | `https://www.banxico.org.mx/SieAPIRest/service/v1/` | Token (header) | Exchange rates, inflation, GDP | MEDIUM |

**No API available (PDF/manual only):** CONEVAL, CONADE, IMSS/ISSSTE, SIIPP-G

### Tier 3 -- US APIs

| Source | API Base URL | Auth | Data | Priority |
|--------|-------------|------|------|----------|
| Census Bureau | `https://api.census.gov/data/` | API key (optional) | ACS, Decennial, demographics | HIGH |
| BLS | `https://api.bls.gov/publicAPI/v2/timeseries/data/` | API key | Employment, wages, CPI | HIGH |
| USAspending | `https://api.usaspending.gov/api/v2/` | None | Federal grants, contracts, spending | HIGH |
| FRED | (same as Tier 1) | API key | Economic indicators | HIGH |
| College Scorecard | `https://api.data.gov/ed/collegescorecard/v1/schools` | API key | Higher education outcomes | MEDIUM |
| HUD | `https://www.huduser.gov/hudapi/public/` | Token | Fair Market Rent, income limits, housing | MEDIUM |
| CDC WONDER | `https://wonder.cdc.gov/` | None | Mortality, disease, public health | MEDIUM |
| EPA Envirofacts | `https://data.epa.gov/efservice/` | API key | Environmental quality, compliance | LOW |

### Tier 4 -- User-Provided Data (Always Available)

- **CSV/Excel upload** -- athlete metrics, student grades, beneficiary records
- **PDF upload** -- evaluation reports, program documents, policy briefs
- **MCP bridges** -- user-registered external data sources (extensible)

---

## 3. Evaluation Methodology

### Regulatory Frameworks

**Mexico (CONEVAL):**
- Marco Logico (MIR): Fin / Proposito / Componentes / Actividades
- PbR-SED: Results-Based Budgeting + Performance Evaluation System
- 6 evaluation types: Diseno, Consistencia y Resultados (ECR), Procesos, Indicadores, Impacto, Estrategicas
- CREMAA indicator criteria: Claridad, Relevancia, Economia, Monitoreable, Adecuado, Aportacion marginal

**US (Federal):**
- Evidence Act 2018: systematic evidence-building plans
- GPRA Modernization Act: integrated performance frameworks
- WWC Standards v5.0: 4-tier evidence hierarchy (Strong, Moderate, Promising, Rationale)
- GAO evaluation standards: transparent documentation and public reporting

### Causal Inference Methods (Tools to Build)

| Method | When Used | Key Assumptions | Evidence Strength |
|--------|-----------|-----------------|-------------------|
| RCT analysis | Random assignment data available | SUTVA, no spillovers | Gold standard |
| Difference-in-Differences (DiD) | Pre/post data, treatment/control groups | Parallel trends | High |
| Regression Discontinuity (RDD) | Sharp eligibility cutoff exists | Continuity at threshold | High |
| Propensity Score Matching (PSM) | Rich covariate data, no random assignment | Selection on observables | Moderate-High |
| Synthetic Control | Single treated unit, multiple controls | Weighted combination matches pre-treatment | Moderate |
| Instrumental Variables (IV) | Valid instrument exists | Exclusion restriction | Moderate-High |

### Evidence Grading

Extend existing GRADE implementation to social program context:
- **Certainty of evidence:** high / moderate / low / very low
- **Downgrading factors:** risk of bias, inconsistency, indirectness, imprecision, publication bias
- **Upgrading factors:** large effect, dose-response, plausible confounding
- **WWC tier mapping:** Tier 1 (strong) through Tier 4 (rationale)

---

## 4. Server Architecture

### New Bounded Context: `impact/`

```
server/src/ehrlich/impact/
  domain/
    entities.py          # Program, Indicator, Beneficiary, CausalEstimate, ThreatToValidity
    repository.py        # ProgramDataRepository, IndicatorRepository ABCs
    ports.py             # CausalEstimator, DataHarmonizer, CostAnalyzer ABCs
    dri.py               # (n/a -- equivalent would be evaluation_standards.py)
    evaluation_standards.py  # CONEVAL ECR template, WWC tiers, GRADE criteria
  application/
    impact_service.py    # Core service: causal estimation, evidence grading, benchmarking
  infrastructure/
    inegi_client.py      # INEGI Indicadores + DENUE APIs
    datos_gob_client.py  # datos.gob.mx CKAN API
    transparencia_client.py  # Transparencia Presupuestaria API
    banxico_client.py    # Banxico SIE API
    census_client.py     # US Census Bureau API
    bls_client.py        # Bureau of Labor Statistics API
    usaspending_client.py  # USAspending.gov API
    worldbank_client.py  # World Bank API
    who_client.py        # WHO GHO API
    fred_client.py       # FRED API (already used in other contexts? no -- new)
    data_harmonizer.py   # Merge datasets by geography/time period
    csv_parser.py        # Parse user-uploaded CSV/Excel files
    pdf_extractor.py     # Extract text from uploaded PDFs
  tools.py               # Impact evaluation tools
```

### Domain Entities

```python
@dataclass
class Program:
    name: str
    description: str
    country: str  # ISO 3166-1 alpha-2
    region: str   # state/province
    sector: str   # education, health, sports, employment, housing
    start_date: str
    end_date: str | None
    budget: float | None
    currency: str
    beneficiary_count: int | None
    indicators: list[Indicator]

@dataclass(frozen=True)
class Indicator:
    name: str
    level: str  # fin, proposito, componente, actividad (MIR) or outcome, output, activity (generic)
    unit: str
    baseline: float | None
    target: float | None
    actual: float | None
    period: str

@dataclass(frozen=True)
class CausalEstimate:
    method: str  # did, psm, rdd, synthetic_control, iv, rct
    effect_size: float
    standard_error: float
    confidence_interval: tuple[float, float]
    p_value: float
    n_treatment: int
    n_control: int
    covariates: list[str]
    assumptions: list[str]
    threats: list[ThreatToValidity]
    evidence_tier: str  # strong, moderate, promising, rationale

@dataclass(frozen=True)
class ThreatToValidity:
    type: str  # selection_bias, attrition, history, maturation, spillover, contamination
    severity: str  # high, moderate, low
    description: str
    mitigation: str | None

@dataclass(frozen=True)
class Benchmark:
    source: str  # worldbank, who, inegi, literature
    indicator: str
    value: float
    unit: str
    geography: str
    period: str
    url: str | None
```

### Tools (Proposed: ~18 new tools)

**Data Access (6):**
- `search_census_data` -- Query INEGI or US Census by indicator/geography/period
- `search_economic_indicators` -- Query FRED, Banxico, World Bank time series
- `search_budget_data` -- Query Transparencia Presupuestaria or USAspending
- `search_health_indicators` -- Query WHO GHO or CDC WONDER
- `search_open_data` -- Query datos.gob.mx or data.gov CKAN portals
- `fetch_benchmark` -- Get comparison value from international sources (World Bank, OECD)

**Causal Inference (5):**
- `estimate_did` -- Difference-in-differences with parallel trends test
- `estimate_psm` -- Propensity score matching with balance diagnostics
- `estimate_rdd` -- Regression discontinuity (sharp/fuzzy)
- `estimate_synthetic_control` -- Synthetic control method
- `assess_threats` -- Automated threat-to-validity assessment

**Program Analysis (4):**
- `analyze_program_indicators` -- MIR/logical framework indicator analysis with CREMAA validation
- `compute_cost_effectiveness` -- Cost per unit outcome, ICER
- `compare_programs` -- Cross-program or cross-region comparison with statistical tests
- `analyze_beneficiary_data` -- Descriptive + inferential analysis of beneficiary records

**Document Processing (3):**
- `extract_program_data` -- Parse uploaded PDF/CSV and extract structured program data
- `extract_mir` -- Extract MIR (Matriz de Indicadores) from evaluation documents
- `generate_evaluation_report` -- Format findings into CONEVAL ECR or WWC-compliant template

### Visualization Tools (Proposed: ~6 new viz tools)

- `render_causal_diagram` -- DAG showing treatment, outcome, confounders
- `render_parallel_trends` -- Pre/post treatment vs control trends (DiD visual)
- `render_rdd_plot` -- Regression discontinuity scatter with cutoff
- `render_program_dashboard` -- Multi-indicator KPI dashboard
- `render_cost_effectiveness` -- Cost-effectiveness frontier chart
- `render_geographic_comparison` -- State/region comparison bar chart with benchmarks

---

## 5. Domain Config

```python
IMPACT_EVALUATION = DomainConfig(
    name="Impact Evaluation",
    description="Hypothesis-driven causal analysis of social programs",
    tool_tags=frozenset({
        "impact",       # core impact evaluation tools
        "census",       # INEGI, Census Bureau
        "economic",     # FRED, Banxico, World Bank
        "budget",       # Transparencia Presupuestaria, USAspending
        "health",       # WHO, CDC
        "opendata",     # datos.gob.mx, data.gov
        "statistics",   # existing statistical testing tools
        "literature",   # existing literature search
        "ml",           # existing generic ML tools
        "visualization" # viz tools
    }),
    score_definitions=[
        ScoreDefinition(
            name="effect_size",
            description="Standardized effect size (Cohen's d, odds ratio, or beta coefficient)"
        ),
        ScoreDefinition(
            name="statistical_significance",
            description="P-value from causal inference method"
        ),
        ScoreDefinition(
            name="evidence_tier",
            description="WWC evidence tier: strong (RCT), moderate (quasi-experimental), promising (correlational), rationale (logic model)"
        ),
        ScoreDefinition(
            name="cost_effectiveness",
            description="Cost per unit outcome improvement"
        ),
    ],
    experiment_examples=[
        # DiD example
        """Experiment: Does conditional cash transfer reduce school dropout?
        Method: Difference-in-differences
        Steps:
        1. search_census_data(indicator="school_enrollment", geography="sonora", years="2018-2024")
        2. search_census_data(indicator="school_enrollment", geography="chihuahua", years="2018-2024")  # control
        3. estimate_did(treatment_data=sonora, control_data=chihuahua, treatment_start="2021")
        4. assess_threats(method="did", data=results)
        5. fetch_benchmark(indicator="dropout_rate", source="worldbank", country="MX")""",

        # PSM example
        """Experiment: Does sports scholarship improve competition performance?
        Method: Propensity score matching
        Steps:
        1. extract_program_data(file="athletes_2025.csv")
        2. estimate_psm(treatment="scholarship_recipient", outcome="competition_rank", covariates=["age", "sport", "baseline_rank"])
        3. assess_threats(method="psm", data=results)
        4. compute_cost_effectiveness(program_cost=budget, outcome_improvement=effect)""",

        # RDD example
        """Experiment: Does eligibility threshold for housing subsidy improve outcomes?
        Method: Regression discontinuity
        Steps:
        1. search_budget_data(program="housing_subsidy", year="2024")
        2. extract_program_data(file="beneficiaries.csv")
        3. estimate_rdd(running_variable="income_score", cutoff=2500, outcome="housing_quality_index")
        4. render_rdd_plot(data=results)"""
    ],
    detection_keywords=[
        "program evaluation", "impact evaluation", "social program",
        "programa social", "evaluacion de impacto", "evaluacion de consistencia",
        "policy evaluation", "cost-effectiveness", "cost-benefit",
        "beneficiaries", "beneficiarios", "CONEVAL", "MIR",
        "difference-in-differences", "propensity score", "regression discontinuity",
        "causal inference", "treatment effect", "counterfactual",
        "public policy", "politica publica", "gobierno", "government program",
        "sports program", "education program", "health program",
        "scholarship", "beca", "subsidio", "subsidy",
        "dropout rate", "desercion", "enrollment", "matricula",
        "INEGI", "census", "censo"
    ]
)
```

---

## 6. Frontend Components

### New Components

| Component | Purpose |
|-----------|---------|
| `FileUpload.tsx` | Drag-and-drop CSV/PDF upload with file type validation |
| `DataPreview.tsx` | Preview uploaded dataset (columns, types, sample rows) |
| `CausalDiagram.tsx` | Interactive DAG (treatment, outcome, confounders) |
| `ParallelTrendsChart.tsx` | DiD visual with pre/post treatment trends |
| `RDDPlot.tsx` | Regression discontinuity scatter with fitted lines |
| `ProgramDashboard.tsx` | Multi-indicator KPI cards with sparklines |
| `CostEffectivenessFrontier.tsx` | Scatter of programs by cost vs outcome |
| `GeographicComparison.tsx` | State/region bar chart with benchmark lines |
| `EvaluationReport.tsx` | CONEVAL ECR or WWC-formatted evaluation report |
| `MIRTable.tsx` | Logical framework matrix (Fin/Proposito/Componentes/Actividades) |
| `ThreatAssessment.tsx` | Validity threats panel with severity badges |

### Modified Components

| Component | Change |
|-----------|--------|
| `PromptInput.tsx` | Add file upload zone (CSV, PDF, Excel) |
| `TemplateCards.tsx` | Add impact evaluation templates (sports program, education, health) |
| `InvestigationReport.tsx` | Add evaluation-specific sections (causal estimates, MIR, threats) |
| `VizRegistry.tsx` | Register 6 new visualization types |

---

## 7. MCP Bridge Strategy

### Pre-built Bridges (ship with platform)

None initially. All Tier 1-3 APIs are direct integrations.

### User-Registerable Bridges (extensible)

Users or organizations register MCP servers for their specific data:

```
# Example: CODESON (Sonora Sports Commission)
ehrlich-mcp-codeson:
  transport: http
  url: https://codeson-data.example.com/mcp
  tools:
    - get_athlete_data
    - get_competition_results
    - get_program_beneficiaries

# Example: Colombian education ministry
ehrlich-mcp-mineducacion:
  transport: http
  url: https://mineducacion-data.example.com/mcp
  tools:
    - get_student_enrollment
    - get_test_scores
    - get_school_infrastructure
```

### MCP Registration UI

New settings page: `/settings/data-sources`
- Add MCP server (URL, transport, auth)
- Test connection
- View available tools
- Tag tools with domain tags for auto-discovery

---

## 8. Document Upload Architecture

### API Endpoints

```
POST /api/v1/investigate
  Content-Type: multipart/form-data
  Fields:
    - prompt: string (research question)
    - director_model: string (haiku/sonnet/opus)
    - files[]: File[] (CSV, PDF, XLSX -- max 10 files, 50MB total)

POST /api/v1/upload
  Content-Type: multipart/form-data
  Fields:
    - file: File
  Response:
    - file_id: string
    - filename: string
    - content_preview: string (first 500 chars of extracted text)
    - columns: string[] (for CSV/Excel)
    - row_count: int (for CSV/Excel)
```

### Processing Pipeline

```
File upload
  -> Type detection (CSV, PDF, XLSX)
  -> CSV/XLSX: parse with pandas, return schema + preview
  -> PDF: extract text with pymupdf, summarize with Haiku if >4000 chars
  -> Inject into Director prompt as <uploaded_data> XML block
  -> For CSV: include column names, dtypes, summary statistics, sample rows
  -> For PDF: include extracted/summarized text
```

### Dependencies

- `pymupdf` (fitz) -- PDF text extraction (BSD license, no system deps)
- `openpyxl` -- Excel file reading (MIT license)
- `pandas` -- CSV/Excel parsing + descriptive statistics (already indirect dep via scipy)

---

## 9. Differentiation Summary

| Dimension | Traditional M&E | General AI (ChatGPT) | Ehrlich Impact Evaluation |
|-----------|----------------|----------------------|---------------------------|
| Hypothesis formulation | Manual | User-guided | Autonomous (Director) |
| Causal inference | None | Manual code | Built-in tools (DiD, PSM, RDD) |
| Public data APIs | None | None | 15+ integrated sources |
| Evidence grading | None | None | GRADE + WWC tiers |
| Multi-model | N/A | Single LLM | Director-Worker-Summarizer |
| Time to result | Months/years | Hours (manual) | Minutes (autonomous) |
| Cost | $4K-$14K/year + consultants | API costs | Credit-based ($1-5 per investigation) |
| Mexico compliance | Some (CONEVAL) | None | MIR, ECR, PbR-SED templates |
| US compliance | Some | None | WWC tiers, Evidence Act alignment |

---

## 10. Implementation Phases

### Phase 1: Foundation (document upload + universal APIs)
- File upload API (CSV, PDF, Excel)
- `extract_program_data` tool
- World Bank, FRED, WHO API clients
- Basic `compare_programs` tool using existing `run_statistical_test`
- 2 new viz tools: `render_program_dashboard`, `render_geographic_comparison`

### Phase 2: Causal Inference Engine
- `estimate_did`, `estimate_psm`, `estimate_rdd` tools
- `assess_threats` automated validity assessment
- `compute_cost_effectiveness` tool
- 3 new viz tools: `render_parallel_trends`, `render_rdd_plot`, `render_causal_diagram`

### Phase 3: Mexico Integration
- INEGI Indicadores + DENUE clients
- datos.gob.mx CKAN client
- Transparencia Presupuestaria client
- Banxico SIE client
- `extract_mir` tool + `MIRTable.tsx` component
- CONEVAL ECR report template

### Phase 4: US Integration
- Census Bureau client
- BLS client
- USAspending client
- College Scorecard client
- WWC evidence tier classification
- US-formatted evaluation report template

### Phase 5: MCP Bridge Self-Service
- User MCP registration UI
- Connection testing
- Tool auto-discovery and tagging
- Per-organization data source management

---

## References

- [CONEVAL Evaluation Process](https://www.coneval.org.mx/Evaluacion/Paginas/Proceso-de-Evaluacion.aspx)
- [WWC Standards Handbook v5.0](https://ies.ed.gov/ncee/wwc/Docs/referenceresources/Final_WWC-HandbookVer5.0-0-508.pdf)
- [Evidence Act 2018](https://www.congress.gov/bill/115th-congress/house-bill/4174)
- [INEGI API](https://www.inegi.org.mx/servicios/api_indicadores.html)
- [Census Bureau API](https://api.census.gov/data/)
- [World Bank API](https://api.worldbank.org/v2/)
- [FRED API](https://api.stlouisfed.org/fred/)
- [CGD: Only 11 Impact Evaluations out of 2,800](https://pubs.cgdev.org/evidence-to-impact/1-progress-and-challenges/challenges/index.html)
- See also: `docs/competitive-landscape-social-programs.md`, `docs/us-public-data-apis.md`

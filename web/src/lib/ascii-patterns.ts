/**
 * ASCII art backgrounds for the Lab Protocol landing page.
 * Rendered at 3% opacity as monospace pre-formatted text.
 * Each pattern is designed to tile or fill a section background.
 */

/** Hero: domain-agnostic investigation protocol and scientific notation */
export const HERO_ASCII = `
  ┌─ INVESTIGATION PROTOCOL ────────────────────────────┐
  │  P(H|E) = P(E|H) · P(H) / P(E)                    │
  │  prior: 0.65  →  posterior: 0.89                    │
  │  status: SUPPORTED   evidence: 4/5 concordant       │
  └─────────────────────────────────────────────────────┘

  PHASE  01 ──→ 02 ──→ 03 ──→ 04 ──→ 05 ──→ 06
         PICO   LIT    FORM   TEST   CTRL   SYNTH

  ┌─ HYPOTHESIS ──────────────┐  ┌─ EXPERIMENT ────────────┐
  │  prediction: μ₁ > μ₂     │  │  IV: treatment          │
  │  null: μ₁ = μ₂           │  │  DV: outcome_measure    │
  │  criteria: Δ > threshold  │  │  controls: [pos, neg]   │
  │  prior: 0.65              │  │  analysis: Bayes + freq │
  └───────────────────────────┘  └─────────────────────────┘

  H₀: μ₁ = μ₂     H₁: μ₁ ≠ μ₂     α = 0.05

  effect_size = (M₁ - M₂) / SD_pooled
  Z' = 1 - (3·σ₊ + 3·σ₋) / |μ₊ - μ₋|

  ┌──────┬──────┬──────┬──────┬──────┬──────┐
  │ TOOL │ TOOL │ TOOL │ TOOL │ TOOL │ TOOL │
  │  01  │  02  │  03  │  ...  │  47  │  48  │
  └──────┴──────┴──────┴──────┴──────┴──────┘

  GRADE: ⊕⊕⊕⊕ HIGH  │  PICO: P-I-C-O  │  AMSTAR-2
`.trim();

/** Architecture: data flow and pipeline notation */
export const ARCHITECTURE_ASCII = `
  ┌─────────────┐          ┌─────────────┐
  │   DIRECTOR  │──────────│  FORMULATE  │
  │  opus-4.6   │          │ hypotheses  │
  └──────┬──────┘          └─────────────┘
         │
    ┌────┴────┐
    ▼         ▼
  ┌───┐     ┌───┐    asyncio.Queue
  │R01│     │R02│    ═══════════════
  │snт│     │snт│    batch_size = 2
  └─┬─┘     └─┬─┘    max_iter = 10
    │         │
    ▼         ▼       tool_calls: 65
  ┌─────────────┐     domains: 3
  │ SUMMARIZER  │     sources: 15
  │  haiku-4.5  │
  └─────────────┘

  tokens_in ──→ cache_read ──→ cache_write
  $0.003/1K     $0.0003/1K    $0.00375/1K
`.trim();

/** Methodology: scientific notation and formulas */
export const METHODOLOGY_ASCII = `
  ═══════════════════════════════════════════════
  PHASE 1    PHASE 2    PHASE 3    PHASE 4
  classify   survey     formulate  execute
  ───────    ───────    ────────   ───────
  PICO       GRADE      Popper     Fisher
  domain     AMSTAR-2   Platt      controls
  detect     snowball   Bayes      confounders
  ═══════════════════════════════════════════════

  H₀: μ₁ = μ₂     H₁: μ₁ ≠ μ₂     α = 0.05

  effect_size = (M₁ - M₂) / SD_pooled

  P(H|E) ∝ P(E|H) · P(H)

  Z' = 1 - (3·σ₊ + 3·σ₋) / |μ₊ - μ₋|
`.trim();

/** Data sources: table-style readout */
export const DATA_SOURCES_ASCII = `
  ┌────────────────┬──────────────┬────────┐
  │ SOURCE         │ ENDPOINT     │ STATUS │
  ├────────────────┼──────────────┼────────┤
  │ ChEMBL         │ /chembl/api  │   OK   │
  │ PubChem        │ /rest/pug    │   OK   │
  │ RCSB PDB       │ /search      │   OK   │
  │ UniProt        │ /uniprot     │   OK   │
  │ Open Targets   │ /graphql     │   OK   │
  │ EPA CompTox    │ /api-ccte    │   OK   │
  │ GtoPdb         │ /services    │   OK   │
  │ ClinicalTrials │ /api/v2      │   OK   │
  │ NIH DSLD       │ /dsld/v9     │   OK   │
  │ USDA FoodData  │ /fdc/v1      │   OK   │
  │ OpenFDA CAERS  │ /food/event  │   OK   │
  │ Ehrlich FTS5   │ local.db     │   OK   │
  └────────────────┴──────────────┴────────┘

  ping: 12ms  cache_hit_rate: 0.847  uptime: 99.97%
`.trim();

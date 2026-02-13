export const STATS = {
  tools: 67,
  dataSources: 16,
  domains: 3,
  models: 3,
  phases: 6,
  vizTools: 12,
  externalAPIs: 15,
  boundedContexts: 10,
  sseEvents: 20,
} as const;

export const NAV_LINKS = [
  { label: "How It Works", href: "#how-it-works" },
  { label: "Architecture", href: "#architecture" },
  { label: "Domains", href: "#domains" },
  { label: "Who It's For", href: "#who-its-for" },
  { label: "Pricing", href: "#pricing" },
  { label: "GitHub", href: "https://github.com/sequelcore/ehrlich" },
] as const;

export const FOOTER_LINKS = {
  product: [
    { label: "Console", href: "/console" },
    { label: "Methodology", href: "/console/methodology" },
    { label: "Pricing", href: "#pricing" },
  ],
  developers: [
    { label: "GitHub", href: "https://github.com/sequelcore/ehrlich" },
    { label: "Documentation", href: "/docs" },
    { label: "Contributing", href: "https://github.com/sequelcore/ehrlich/blob/main/CONTRIBUTING.md" },
  ],
  legal: [
    { label: "AGPL-3.0 License", href: "https://github.com/sequelcore/ehrlich/blob/main/LICENSE" },
    { label: "Commercial License", href: "mailto:ricardo@sequel.com" },
  ],
} as const;

export const EXAMPLE_PROMPTS = [
  "Find antimicrobial compounds effective against MRSA with low resistance risk",
  "Compare HIIT vs steady-state training for VO2max in adults over 40",
  "Evaluate creatine monohydrate for strength performance and safety",
  "Identify microplastic degradation products with high aquatic toxicity",
] as const;

export const DIFFERENTIATORS = [
  {
    label: "Real Computation",
    tagline: "70 tools that compute, not summarize.",
    description:
      "Ehrlich trains ML models, runs molecular docking, executes statistical tests, and validates with negative controls. Every tool returns structured data from real computation or real APIs.",
    capabilities: [
      "RDKit molecular descriptors + fingerprints",
      "XGBoost + Chemprop with scaffold-split validation",
      "AutoDock Vina molecular docking",
      "scipy.stats hypothesis testing (t-test, Mann-Whitney, Fisher)",
      "Z'-factor assay quality + permutation significance",
    ],
  },
  {
    label: "Accessible Pricing",
    tagline: "$2-10 per investigation. Free tier included.",
    description:
      "Full 6-phase methodology, all 70 tools, all 16 data sources at every tier. No feature gates. A student in Mexico and a pharma lab in Boston use the same product. The only variable is model quality.",
    capabilities: [
      "3 domains, extensible to any",
      "Free: 3 Haiku investigations/month",
      "Credits: Haiku (1), Sonnet (3), Opus (5)",
      "Enterprise: bring your own Anthropic key",
      "AGPL-3.0: self-host, modify, extend",
    ],
  },
  {
    label: "Structured Methodology",
    tagline: "Popper, Fisher, GRADE. Not conversation.",
    description:
      "Every investigation follows a 6-phase protocol with falsifiable hypotheses, controlled experiments, evidence hierarchies, and GRADE certainty grading. Findings link to real source IDs. You approve hypotheses before testing begins.",
    capabilities: [
      "Falsifiable hypotheses with predictions + criteria",
      "Controlled experiments with confounders + analysis plans",
      "8-tier evidence hierarchy with source provenance",
      "GRADE certainty grading on final synthesis",
      "User approval gate before experiment execution",
    ],
  },
] as const;

export const DOMAINS = [
  {
    label: "MOLECULAR SCIENCE",
    toolCount: 22,
    description:
      "Drug discovery, antimicrobial resistance, environmental toxicology, agricultural biocontrol.",
    capabilities: [
      "RDKit cheminformatics (descriptors, fingerprints, 3D conformers)",
      "ChEMBL bioactivity screening (MIC, Ki, IC50, EC50)",
      "AutoDock Vina molecular docking",
      "ADMET profiling + Lipinski drug-likeness",
      "EPA CompTox environmental toxicity",
      "PDB protein targets + UniProt annotations",
    ],
    sources: "ChEMBL, PubChem, RCSB PDB, UniProt, Open Targets, EPA CompTox, GtoPdb",
    prompt: "Find compounds effective against carbapenem-resistant Klebsiella with favorable ADMET profiles",
    vizTools: ["Binding scatter", "ADMET radar", "Forest plot", "Evidence matrix"],
  },
  {
    label: "TRAINING SCIENCE",
    toolCount: 11,
    description:
      "Exercise physiology, protocol optimization, injury risk assessment, clinical trial evidence.",
    capabilities: [
      "Pooled effect sizes + heterogeneity analysis",
      "Protocol comparison with composite scoring",
      "Injury risk scoring (sport, load, history, age)",
      "ACWR, monotony, strain, session RPE metrics",
      "ClinicalTrials.gov + PubMed with MeSH terms",
      "Banister fitness-fatigue performance modeling",
    ],
    sources: "ClinicalTrials.gov, PubMed, wger, Semantic Scholar",
    prompt: "Compare periodized vs non-periodized resistance training in trained athletes",
    vizTools: ["Training timeline", "Muscle heatmap", "Performance chart", "Dose-response"],
  },
  {
    label: "NUTRITION SCIENCE",
    toolCount: 10,
    description:
      "Supplement evidence, nutrient adequacy, drug interactions, inflammatory scoring, safety monitoring.",
    capabilities: [
      "NIH DSLD supplement label ingredient lookup",
      "USDA FoodData nutrient profiling",
      "DRI-based adequacy (EAR/RDA/AI/UL)",
      "Drug-supplement interaction screening (RxNav)",
      "OpenFDA CAERS adverse event monitoring",
      "Dietary Inflammatory Index (DII) scoring",
    ],
    sources: "NIH DSLD, USDA FoodData, OpenFDA CAERS, RxNav",
    prompt: "Assess safety and efficacy of vitamin D3 + K2 supplementation at high doses",
    vizTools: ["Nutrient comparison", "Nutrient adequacy", "Therapeutic window", "Funnel plot"],
  },
] as const;

export const DATA_SOURCES = [
  { name: "ChEMBL", domain: "ebi.ac.uk/chembl", access: "Free" as const, records: "2.5M compounds", purpose: "Bioactivity data for any assay type" },
  { name: "Semantic Scholar", domain: "api.semanticscholar.org", access: "Free" as const, records: "200M+ papers", purpose: "Literature search + citation chasing" },
  { name: "RCSB PDB", domain: "data.rcsb.org", access: "Free" as const, records: "200K+ structures", purpose: "Protein target discovery" },
  { name: "PubChem", domain: "pubchem.ncbi.nlm.nih.gov", access: "Free" as const, records: "100M+ compounds", purpose: "Compound search by target/activity" },
  { name: "EPA CompTox", domain: "api-ccte.epa.gov", access: "API Key" as const, records: "1M+ chemicals", purpose: "Environmental toxicity + bioaccumulation" },
  { name: "UniProt", domain: "rest.uniprot.org", access: "Free" as const, records: "250M+ sequences", purpose: "Protein function + disease associations" },
  { name: "Open Targets", domain: "api.platform.opentargets.org", access: "Free" as const, records: "12K+ targets", purpose: "Disease-target associations (scored)" },
  { name: "GtoPdb", domain: "guidetopharmacology.org", access: "Free" as const, records: "Curated", purpose: "Expert pharmacology (pKi, pIC50)" },
  { name: "ClinicalTrials.gov", domain: "clinicaltrials.gov/api", access: "Free" as const, records: "500K+ studies", purpose: "Exercise/training RCT evidence" },
  { name: "PubMed", domain: "eutils.ncbi.nlm.nih.gov", access: "Free" as const, records: "36M+ articles", purpose: "Biomedical literature with MeSH" },
  { name: "wger", domain: "wger.de/api/v2", access: "Free" as const, records: "800+ exercises", purpose: "Exercise database (muscles, equipment)" },
  { name: "NIH DSLD", domain: "api.ods.od.nih.gov", access: "Free" as const, records: "180K+ products", purpose: "Supplement label ingredients" },
  { name: "USDA FoodData", domain: "api.nal.usda.gov", access: "API Key" as const, records: "300K+ foods", purpose: "Nutrient profiles (macro + micro)" },
  { name: "OpenFDA CAERS", domain: "api.fda.gov", access: "Free" as const, records: "Ongoing", purpose: "Supplement adverse event reports" },
  { name: "RxNav", domain: "rxnav.nlm.nih.gov", access: "Free" as const, records: "RxNorm DB", purpose: "Drug-nutrient interaction screening" },
  { name: "Ehrlich FTS5", domain: "internal", access: "Internal" as const, records: "Growing", purpose: "Past findings (institutional memory)" },
] as const;

export const METHODOLOGY_PHASES = [
  {
    number: "01",
    label: "Classification & PICO",
    foundation: "Sackett (1996)",
    description: "Decompose your question into Population, Intervention, Comparison, Outcome. Auto-detect domains. Multi-domain questions merge configs automatically.",
  },
  {
    number: "02",
    label: "Literature Survey",
    foundation: "GRADE + AMSTAR-2",
    description: "Systematic search with citation chasing. GRADE-adapted evidence grading. AMSTAR-2 quality self-assessment. Haiku compresses and classifies.",
  },
  {
    number: "03",
    label: "Hypothesis Formulation",
    foundation: "Popper + Platt + Bayes",
    description: "Falsifiable hypotheses with predictions, null predictions, success/failure criteria, scope, type, and prior confidence. You approve before testing starts.",
  },
  {
    number: "04",
    label: "Experiment Execution",
    foundation: "Fisher (1935)",
    description: "Experiments with independent/dependent variables, controls, confounders, and analysis plans. 2 experiments run in parallel. 70 tools across all domains.",
  },
  {
    number: "05",
    label: "Validation & Controls",
    foundation: "Zhang (1999) + Y-scrambling",
    description: "Negative controls with known-inactive compounds. Z'-factor assay quality. Permutation significance testing. Scaffold-split vs random-split comparison.",
  },
  {
    number: "06",
    label: "Synthesis",
    foundation: "GRADE synthesis",
    description: "Certainty grading (5 downgrading + 3 upgrading domains). Priority tiers. Limitations taxonomy. Knowledge gap analysis. Follow-up recommendations.",
  },
] as const;

export const VISUALIZATION_CATEGORIES = [
  {
    label: "3D Molecular Viewers",
    tech: "3Dmol.js WebGL",
    items: [
      "Live Lab Viewer -- SSE-driven scene: protein targets load, ligands dock, candidates color by score",
      "3D Conformer Viewer -- MMFF94-optimized 3D structures with interactive rotate/zoom",
      "Docking Viewer -- Protein + ligand overlay showing binding pocket and interactions",
    ],
  },
  {
    label: "Statistical Charts",
    tech: "Recharts + Visx",
    items: [
      "Forest Plot -- Meta-analysis effect sizes with confidence intervals",
      "Funnel Plot -- Publication bias assessment across studies",
      "Dose-Response Curve -- Dose-response with confidence band (Visx)",
      "Evidence Matrix -- Hypothesis-by-evidence heatmap (Visx)",
    ],
  },
  {
    label: "Domain-Specific Charts",
    tech: "Recharts + Custom SVG",
    items: [
      "Binding Scatter -- Compound binding affinities across targets",
      "ADMET Radar -- Drug-likeness property profiles (6 axes)",
      "Training Timeline -- Training load with ACWR danger zones + brush",
      "Performance Chart -- Banister fitness-fatigue model (CTL/ATL/TSB)",
      "Muscle Heatmap -- Anatomical front/back body diagram with activation intensity",
      "Nutrient Comparison -- Grouped bar chart comparing foods",
      "Nutrient Adequacy -- Horizontal bars showing % RDA with MAR score",
      "Therapeutic Window -- EAR/RDA/UL safety zones per nutrient",
    ],
  },
  {
    label: "Investigation UI",
    tech: "React Flow + Custom",
    items: [
      "Investigation Diagram -- Hypothesis/experiment/finding node graph with status colors and revision edges",
      "Hypothesis Board -- Kanban grid with expandable confidence bars and approval cards",
      "Candidate Table -- Thumbnail grid with 2D SVG + expandable 3D viewer + Lipinski badge",
      "Candidate Comparison -- Side-by-side scoring view for 2-4 candidates with best-in-group highlighting",
      "Investigation Report -- 8-section structured report with full audit trail and markdown export",
    ],
  },
] as const;

export const PLANNED_FEATURES = [
  {
    label: "Materials Science",
    type: "domain" as const,
    description: "Alloy design, polymer properties, crystal structure prediction. ICSD, Materials Project, AFLOW databases.",
  },
  {
    label: "Genomics",
    type: "domain" as const,
    description: "Gene expression analysis, variant interpretation, pathway enrichment. NCBI, Ensembl, UniProt cross-referencing.",
  },
  {
    label: "Environmental Science",
    type: "domain" as const,
    description: "Pollution monitoring, climate data analysis, biodiversity assessment. EPA, NOAA, GBIF integration.",
  },
  {
    label: "MCP Ecosystem",
    type: "feature" as const,
    description: "Connect external MCP servers as tool providers. Community-built domains plug in without code changes to the core engine.",
  },
  {
    label: "REST API",
    type: "feature" as const,
    description: "Programmatic access to investigations. Start, monitor, and retrieve results via API. Webhook notifications on completion.",
  },
  {
    label: "Multi-Provider",
    type: "feature" as const,
    description: "Swap the Director, Researcher, or Summarizer to any LLM provider. OpenAI, Google, open-weight models. Mix providers per role for cost or capability.",
  },
  {
    label: "Team Collaboration",
    type: "feature" as const,
    description: "Shared investigations, commenting, branching hypotheses. Build on each other's findings across your research group.",
  },
] as const;

export const PRICING_TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    credits: "3 Haiku investigations/month",
    description: "Full methodology. All 70 tools. All 16 data sources. Findings indexed for future research.",
    features: [
      "Full 6-phase scientific methodology",
      "All 70 tools, all 16 data sources",
      "Full audit trail and report",
      "Self-referential search (FTS5)",
      "No feature gates",
    ],
    cta: "Start Free",
    highlight: false,
  },
  {
    name: "Credits",
    price: "Pay-as-you-go",
    period: "",
    credits: "Choose model quality per investigation",
    description: "Haiku (1 credit), Sonnet (3), Opus (5). Buy packs: 5/25/50 credits with volume discounts up to 30%.",
    features: [
      "Haiku = 1 credit, Sonnet = 3, Opus = 5",
      "Starter: 5 credits",
      "Researcher: 25 credits (20% off)",
      "Lab: 50 credits (30% off)",
      "Credits valid for 60 days",
    ],
    cta: "Buy Credits",
    highlight: true,
  },
  {
    name: "Monthly",
    price: "30 credits/mo",
    period: "33% discount",
    credits: "Auto-refill. Best for active researchers.",
    description: "30 credits auto-refill monthly at the best rate. Mix Haiku, Sonnet, and Opus as needed.",
    features: [
      "30 credits auto-refill monthly",
      "33% discount vs pay-as-you-go",
      "Mix models per investigation",
      "Priority in queue",
      "Cancel anytime",
    ],
    cta: "Subscribe",
    highlight: false,
  },
  {
    name: "Enterprise",
    price: "BYOK",
    period: "",
    credits: "Unlimited. Your API key.",
    description: "Bring Your Own Key. Use your Anthropic API key directly. Platform fee for tools + methodology engine.",
    features: [
      "Your own Anthropic API key",
      "Commercial license (AGPL exemption)",
      "Custom domain development",
      "Self-hosted deployment",
      "Priority support + SLA",
    ],
    cta: "Contact Us",
    highlight: false,
  },
] as const;

export const STATS = {
  tools: 48,
  dataSources: 13,
  domains: 3,
  models: 3,
  phases: 6,
} as const;

export const NAV_LINKS = [
  { label: "Architecture", href: "#architecture" },
  { label: "Methodology", href: "#methodology" },
  { label: "Domains", href: "#domains" },
  { label: "Data Sources", href: "#data-sources" },
  { label: "GitHub", href: "https://github.com" },
] as const;

export const FOOTER_LINKS = [
  { label: "GitHub", href: "https://github.com" },
  { label: "Docs", href: "/docs" },
  { label: "Contributing", href: "https://github.com" },
  { label: "Changelog", href: "/changelog" },
] as const;

export const DOMAINS = [
  {
    label: "MOLECULAR SCIENCE",
    toolCount: 22,
    capabilities: "Drug discovery · Antimicrobial resistance · Toxicology · Agricultural biocontrol",
    sources: "ChEMBL · PubChem · RCSB PDB · UniProt · Open Targets · EPA CompTox · GtoPdb",
    prompt: "Investigate novel antimicrobial compounds effective against MRSA with low resistance risk",
  },
  {
    label: "TRAINING SCIENCE",
    toolCount: 6,
    capabilities: "Exercise physiology · Protocol optimization · Injury risk · Clinical trials",
    sources: "ClinicalTrials.gov · Semantic Scholar",
    prompt: "Compare evidence for high-intensity interval training vs steady-state cardio for VO2max improvement",
  },
  {
    label: "NUTRITION SCIENCE",
    toolCount: 4,
    capabilities: "Supplement evidence · Dietary analysis · Safety monitoring",
    sources: "NIH DSLD · USDA FoodData · OpenFDA CAERS",
    prompt: "Evaluate the evidence for creatine monohydrate supplementation on strength performance",
  },
] as const;

export const DATA_SOURCES = [
  { name: "ChEMBL", domain: "ebi.ac.uk/chembl", access: "Free" as const },
  { name: "Semantic Scholar", domain: "api.semanticscholar.org", access: "Free" as const },
  { name: "RCSB PDB", domain: "data.rcsb.org", access: "Free" as const },
  { name: "PubChem", domain: "pubchem.ncbi.nlm.nih.gov", access: "Free" as const },
  { name: "EPA CompTox", domain: "api-ccte.epa.gov", access: "API Key" as const },
  { name: "UniProt", domain: "rest.uniprot.org", access: "Free" as const },
  { name: "Open Targets", domain: "api.platform.opentargets.org", access: "Free" as const },
  { name: "GtoPdb", domain: "guidetopharmacology.org", access: "Free" as const },
  { name: "ClinicalTrials.gov", domain: "clinicaltrials.gov/api", access: "Free" as const },
  { name: "NIH DSLD", domain: "api.ods.od.nih.gov", access: "Free" as const },
  { name: "USDA FoodData", domain: "api.nal.usda.gov", access: "API Key" as const },
  { name: "OpenFDA CAERS", domain: "api.fda.gov", access: "Free" as const },
  { name: "Ehrlich FTS5", domain: "localhost (self-referential)", access: "Internal" as const },
] as const;

export const METHODOLOGY_PHASES = [
  { label: "Classification & PICO", icon: "FlaskConical" as const },
  { label: "Literature Survey", icon: "BookOpen" as const },
  { label: "Hypothesis Formulation", icon: "Lightbulb" as const, active: true },
  { label: "Experiment Testing", icon: "TestTubes" as const },
  { label: "Negative Controls", icon: "ShieldCheck" as const },
  { label: "Synthesis", icon: "FileText" as const },
] as const;

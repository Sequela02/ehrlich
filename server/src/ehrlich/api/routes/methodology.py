"""Methodology endpoint -- exposes phases, domains, tools, data sources, models."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ehrlich.api.routes.investigation import _build_domain_registry, _build_registry

router = APIRouter(tags=["methodology"])

# ── Static data tied to orchestrator logic ──────────────────────────────

PHASES: list[dict[str, Any]] = [
    {
        "number": 1,
        "name": "Classification & PICO",
        "description": (
            "Classifies the research question into scientific domains and "
            "decomposes it using the PICO framework (Population, Intervention, "
            "Comparison, Outcome). Determines which tools and data sources apply."
        ),
        "model": "haiku",
    },
    {
        "number": 2,
        "name": "Literature Survey",
        "description": (
            "Searches scientific literature via Semantic Scholar with citation "
            "chasing (snowballing). Grades body of evidence using GRADE-adapted "
            "criteria. Produces a PRISMA-lite transparency report."
        ),
        "model": "haiku",
    },
    {
        "number": 3,
        "name": "Hypothesis Formulation",
        "description": (
            "Formulates falsifiable hypotheses with predictions, null predictions, "
            "success/failure criteria, scope, and prior confidence. Designs "
            "structured experiment protocols with controls and analysis plans."
        ),
        "model": "opus",
    },
    {
        "number": 4,
        "name": "Hypothesis Testing",
        "description": (
            "Executes experiments in parallel batches of 2 using domain-specific "
            "tools. Records findings with evidence types and provenance. Evaluates "
            "hypotheses using Bayesian updating and effect size thresholds."
        ),
        "model": "sonnet",
    },
    {
        "number": 5,
        "name": "Validation Controls",
        "description": (
            "Runs positive and negative controls through trained models. Computes "
            "Z'-factor assay quality, permutation significance (Y-scrambling), "
            "and scaffold-split vs random-split comparison."
        ),
        "model": "sonnet",
    },
    {
        "number": 6,
        "name": "Evidence Synthesis",
        "description": (
            "Synthesizes all evidence with GRADE certainty grading across 5 "
            "downgrading and 3 upgrading domains. Ranks candidates into priority "
            "tiers (1-4), identifies knowledge gaps, and recommends follow-up "
            "experiments."
        ),
        "model": "opus",
    },
]

MODELS: list[dict[str, str]] = [
    {
        "role": "Director",
        "model_id": "claude-opus-4-6",
        "purpose": (
            "Hypothesis formulation, experiment design, evidence evaluation, "
            "and final synthesis. No tool access -- pure reasoning."
        ),
    },
    {
        "role": "Researcher",
        "model_id": "claude-sonnet-4-5-20250929",
        "purpose": (
            "Executes experiments with 42 tools in parallel batches. "
            "Records findings with evidence provenance and citations."
        ),
    },
    {
        "role": "Summarizer",
        "model_id": "claude-haiku-4-5-20251001",
        "purpose": (
            "Compresses large tool outputs, performs PICO decomposition, "
            "domain classification, and evidence grading."
        ),
    },
]

DATA_SOURCES: list[dict[str, str]] = [
    {
        "name": "ChEMBL",
        "url": "https://www.ebi.ac.uk/chembl/api/data",
        "purpose": "Bioactivity data (MIC, IC50, Ki, EC50, Kd)",
        "auth": "none",
        "context": "analysis",
    },
    {
        "name": "Semantic Scholar",
        "url": "https://api.semanticscholar.org/graph/v1",
        "purpose": "Scientific paper search and citation chasing",
        "auth": "none",
        "context": "literature",
    },
    {
        "name": "RCSB PDB",
        "url": "https://search.rcsb.org",
        "purpose": "Protein structure discovery by organism and function",
        "auth": "none",
        "context": "simulation",
    },
    {
        "name": "PubChem",
        "url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug",
        "purpose": "Compound search by target, activity, or similarity",
        "auth": "none",
        "context": "analysis",
    },
    {
        "name": "EPA CompTox",
        "url": "https://api-ccte.epa.gov",
        "purpose": "Environmental toxicity, bioaccumulation, chemical fate",
        "auth": "api_key",
        "context": "simulation",
    },
    {
        "name": "UniProt",
        "url": "https://rest.uniprot.org",
        "purpose": "Protein function, disease associations, GO terms",
        "auth": "none",
        "context": "simulation",
    },
    {
        "name": "Open Targets",
        "url": "https://api.platform.opentargets.org",
        "purpose": "Disease-target associations with scored evidence",
        "auth": "none",
        "context": "simulation",
    },
    {
        "name": "GtoPdb",
        "url": "https://www.guidetopharmacology.org/services",
        "purpose": "Expert-curated pharmacology (pKi, pIC50, receptors)",
        "auth": "none",
        "context": "analysis",
    },
    {
        "name": "ClinicalTrials.gov",
        "url": "https://clinicaltrials.gov/api/v2",
        "purpose": "Registered clinical trials for exercise and training RCTs",
        "auth": "none",
        "context": "training",
    },
    {
        "name": "NIH DSLD",
        "url": "https://api.ods.od.nih.gov/dsld/v9",
        "purpose": "Dietary supplement label database (ingredients, amounts)",
        "auth": "none",
        "context": "nutrition",
    },
    {
        "name": "USDA FoodData",
        "url": "https://api.nal.usda.gov/fdc/v1",
        "purpose": "Nutrient profiles for foods and supplements",
        "auth": "api_key",
        "context": "nutrition",
    },
    {
        "name": "OpenFDA CAERS",
        "url": "https://api.fda.gov/food/event.json",
        "purpose": "Supplement adverse event reports (safety monitoring)",
        "auth": "none",
        "context": "nutrition",
    },
    {
        "name": "Ehrlich FTS5",
        "url": "internal",
        "purpose": "Full-text search of past investigation findings",
        "auth": "none",
        "context": "investigation",
    },
]

# ── Tool context mapping (tag -> display name) ─────────────────────────

_TAG_TO_CONTEXT: dict[str, str] = {
    "chemistry": "Chemistry",
    "literature": "Literature",
    "analysis": "Analysis",
    "prediction": "Prediction",
    "simulation": "Simulation",
    "training": "Training Science",
    "clinical": "Training Science",
    "nutrition": "Nutrition Science",
    "safety": "Nutrition Science",
}


# ── Response model ──────────────────────────────────────────────────────


class ToolInfo(BaseModel):
    name: str
    description: str
    tags: list[str]


class ToolGroup(BaseModel):
    context: str
    tools: list[ToolInfo]


class DomainInfo(BaseModel):
    name: str
    display_name: str
    tool_count: int
    score_definitions: list[dict[str, Any]]
    hypothesis_types: list[str]
    categories: list[str]


class MethodologyResponse(BaseModel):
    phases: list[dict[str, Any]]
    domains: list[DomainInfo]
    tools: list[ToolGroup]
    data_sources: list[dict[str, str]]
    models: list[dict[str, str]]


# ── Endpoint ────────────────────────────────────────────────────────────


@router.get("/methodology")
async def get_methodology() -> MethodologyResponse:
    registry = _build_registry()
    domain_registry = _build_domain_registry()

    # Build domain info from registry
    domains: list[DomainInfo] = []
    for config in domain_registry.all_configs():
        domain_tools = registry.list_tools_for_domain(config.tool_tags)
        domains.append(
            DomainInfo(
                name=config.name,
                display_name=config.display_name,
                tool_count=len(domain_tools),
                score_definitions=[
                    {
                        "key": sd.key,
                        "label": sd.label,
                        "format_spec": sd.format_spec,
                        "higher_is_better": sd.higher_is_better,
                    }
                    for sd in config.score_definitions
                ],
                hypothesis_types=list(config.hypothesis_types),
                categories=list(config.valid_domain_categories),
            )
        )

    # Group tools by context tag
    grouped: dict[str, list[ToolInfo]] = {}
    for schema in registry.list_schemas():
        name = schema["name"]
        desc = schema.get("description", "")
        tags = list(registry._tags.get(name, frozenset()))  # noqa: SLF001
        context = "Investigation"
        for tag in tags:
            if tag in _TAG_TO_CONTEXT:
                context = _TAG_TO_CONTEXT[tag]
                break
        tool_info = ToolInfo(name=name, description=desc, tags=tags)
        grouped.setdefault(context, []).append(tool_info)

    # Sort groups by predefined order
    order = [
        "Chemistry",
        "Literature",
        "Analysis",
        "Prediction",
        "Simulation",
        "Training Science",
        "Nutrition Science",
        "Investigation",
    ]
    tool_groups: list[ToolGroup] = []
    for ctx in order:
        if ctx in grouped:
            tool_groups.append(ToolGroup(context=ctx, tools=grouped[ctx]))

    return MethodologyResponse(
        phases=PHASES,
        domains=domains,
        tools=tool_groups,
        data_sources=DATA_SOURCES,
        models=MODELS,
    )

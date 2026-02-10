# Literature Search — Ensuring Reliable, Cited Science

## The Problem

Claude's training cutoff (~May 2025) means:
- Papers from late 2025/2026 are unknown
- Details from training can be conflated or outdated
- Confident statements may not reflect current consensus

A real scientist doesn't work from memory. They cite papers. Ehrlich should too.

## Three-Layer Reliability Model

### Layer 1: Live Literature Search (Semantic Scholar / PubMed)

**Semantic Scholar API (recommended primary):**
- Free, no auth required for basic usage (100 requests/sec unauthenticated)
- Endpoint: `https://api.semanticscholar.org/graph/v1/paper/search`
- Returns: title, authors, year, abstract, DOI, citation count, fields of study
- Can filter by year, fields of study, open access status

```python
import requests

def search_literature(query: str, year_min: int = 2020, limit: int = 10):
    """Search Semantic Scholar for relevant papers."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "year": f"{year_min}-",
        "fields": "title,authors,year,abstract,citationCount,doi,url",
    }
    resp = requests.get(url, params=params)
    return resp.json().get("data", [])

# Example: Claude searches for MRSA membrane disruption
papers = search_literature("MRSA membrane disruption mechanism antibiotic")
# Returns 10 papers with full abstracts, DOIs, citation counts
```

**PubMed E-utilities (backup / biomedical-specific):**
- Free, no auth for basic (<3 requests/sec, or 10/sec with API key)
- Better for biomedical-specific queries
- Endpoint: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- Two-step: esearch (get IDs) → efetch (get details)

```python
def search_pubmed(query: str, limit: int = 10):
    """Search PubMed for relevant papers."""
    # Step 1: Search
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": limit,
        "retmode": "json",
        "sort": "relevance",
    }
    search_resp = requests.get(search_url, params=search_params).json()
    ids = search_resp["esearchresult"]["idlist"]

    # Step 2: Fetch details
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    return requests.get(fetch_url, params=fetch_params).text
```

### Layer 2: Pre-Loaded Reference Set

Key papers stored as structured data in the MCP server. Always available, verified, no API dependency.

```python
CORE_REFERENCES = {
    "halicin": {
        "title": "A Deep Learning Approach to Antibiotic Discovery",
        "authors": "Stokes et al.",
        "year": 2020,
        "journal": "Cell",
        "doi": "10.1016/j.cell.2020.01.021",
        "key_findings": [
            "D-MPNN model trained on 2,335 molecules",
            "Discovered halicin from Drug Repurposing Hub + ZINC15",
            "Broad-spectrum via membrane disruption mechanism",
            "51.5% true positive rate for top 99 predictions"
        ]
    },
    "abaucin": {
        "title": "Deep learning-guided discovery of an antibiotic targeting Acinetobacter baumannii",
        "authors": "Liu et al.",
        "year": 2023,
        "journal": "Nature Chemical Biology",
        "doi": "10.1038/s41589-023-01349-8",
        "key_findings": [
            "GNN ensemble trained on ~7,500 molecules",
            "Narrow-spectrum: targets only A. baumannii",
            "Mechanism: perturbs lipoprotein trafficking via LolE",
            "Validated in mouse wound infection model"
        ]
    },
    "who_bppl_2024": {
        "title": "WHO bacterial priority pathogens list, 2024",
        "authors": "WHO",
        "year": 2024,
        "doi": "WHO/MHP/HPS/EML/2024.01",
        "key_findings": [
            "24 pathogens across 15 families",
            "Critical: Gram-negative resistant to last-resort antibiotics",
            "Only 4 innovative antibiotics target critical pathogens",
            "Pipeline described as fragile and failing"
        ]
    }
}
```

### Layer 3: Data Grounding

Statistical analysis and ML models are trained on ChEMBL experimental data — real MIC values measured in real labs. Claude's reasoning interprets data, not memory.

- If Claude says "LogP matters" → the chi-squared test or feature importance proves it
- If Claude says "sulfonamide is enriched" → enrichment analysis shows the p-value
- If Claude says "AUC is 0.87" → that's a computed metric, not a guess

## MCP Tool Design

```python
@mcp.tool()
def search_literature(query: str, year_min: int = 2020, limit: int = 10) -> str:
    """Search scientific literature for papers relevant to the current investigation.
    Use this to ground your reasoning in published research.
    Returns titles, abstracts, DOIs, and citation counts."""
    # ... Semantic Scholar API call
    return json.dumps(papers)

@mcp.tool()
def get_reference(key: str) -> str:
    """Retrieve a curated reference from the core set.
    Available keys: halicin, abaucin, who_bppl_2024, etc.
    Returns full citation details and key findings."""
    ref = CORE_REFERENCES.get(key)
    if not ref:
        return f"Reference '{key}' not found. Available: {list(CORE_REFERENCES.keys())}"
    return json.dumps(ref)
```

## How It Changes the Workflow

**Phase 1 (Literature Review):**
```
Claude calls: search_literature("MRSA antibiotic resistance mechanisms 2024")
  → Gets 10 recent papers with abstracts
  → Reads them, synthesizes findings
  → Cites: "Wang et al. (2024, doi:10.1038/...) demonstrated that..."
  → Identifies gaps: "No recent work on thiadiazole scaffolds against MRSA"
```

**Phase 6 (Mechanistic Reasoning):**
```
Claude finds a thiadiazole-pyrimidine candidate
  → Calls: search_literature("thiadiazole metalloenzyme inhibitor antibacterial")
  → Finds: 3 papers showing thiadiazole affinity for metalloenzymes
  → Cites them in the reasoning: "Consistent with Kumar et al. (2023)..."
```

**Phase 10 (Research Report):**
```
Report includes a References section:
  1. Stokes JM et al. (2020) Cell. doi:10.1016/j.cell.2020.01.021
  2. Liu G et al. (2023) Nat Chem Biol. doi:10.1038/s41589-023-01349-8
  3. Wang X et al. (2024) J Med Chem. doi:10.1021/acs.jmedchem...
  ... (all real DOIs from literature search)
```

## Why This Matters for Judges

- **"Impact" (25%):** The output is scientifically credible, not AI hallucination
- **"Opus 4.6 Use" (25%):** Claude synthesizes real literature, not just training knowledge
- **"Depth" (20%):** Real citations show genuine scientific depth
- **"Demo" (30%):** Watching Claude search papers, read abstracts, and cite them in real-time is compelling

## Sources

- Semantic Scholar API: https://api.semanticscholar.org/
- PubMed E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/

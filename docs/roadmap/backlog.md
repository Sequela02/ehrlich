Back to [Roadmap Index](README.md)

# Backlog (Post-Hackathon)

- Phase 11: Investigation Comparison (side-by-side analysis)
- Phase 13C: Mexico Integration (INEGI, datos.gob.mx, Transparencia, Banxico)
- Phase 13D: US Integration (Census, BLS, USAspending, CDC WONDER)
- Phase 13E: MCP Bridge Self-Service
- Competitive Sports Domain
- Batch screening mode (score entire ZINC subsets)
- Automated synthesis lab integration (Emerald Cloud Lab, Strateos)
- Community contributions: new domains, new tools, new data sources
- Rewarded ads for free credits (AdMob/AdSense integration)
- Stripe integration for paid credit packs
- Admin dashboard for usage analytics
- Planner agent (Sonnet 4.5) for experiment design between Director and Researcher
- Reviewer agent (Sonnet 4.5) for findings audit between Researcher and Director
- Full Bayesian surprise scoring for tree search branch selection

---

# Competitive Sports Domain -- TODO

New bounded context for actual competitive sports analytics: game statistics, player performance, team analysis, and sports-specific strategy research.

## Bounded Context: `sports/`

```
server/src/ehrlich/sports/
├── domain/
│   ├── entities.py          # Player, Team, GameStats, SeasonStats, PerformanceMetric
│   └── repository.py        # SportsDataRepository ABC
├── application/
│   └── sports_service.py    # SportsService (stats analysis, performance comparison)
├── infrastructure/
│   └── *_client.py          # API clients for sports data providers
└── tools.py                 # Tools for Claude
```

## Data Sources (Research Needed)
- [ ] Basketball: NBA API / Basketball Reference (player stats, advanced metrics, play-by-play)
- [ ] Soccer/Football: football-data.org or API-Football (match results, player stats, league standings)
- [ ] American Football: NFL data feeds (player stats, play-by-play, combine data)
- [ ] General: ESPN API or Sports Reference family (multi-sport coverage)

## Planned Tools
- [ ] `search_player_stats` -- player statistics by name/team/season (points, assists, rebounds, goals, etc.)
- [ ] `compare_players` -- side-by-side player comparison with advanced metrics
- [ ] `analyze_team_performance` -- team-level analytics (win rate, offensive/defensive efficiency)
- [ ] `search_sports_literature` -- Semantic Scholar + PubMed for sports-specific research (tactics, biomechanics, game theory)
- [ ] `compute_advanced_metrics` -- sport-specific advanced stats (PER, WAR, xG, passer rating, etc.)
- [ ] `analyze_matchup` -- head-to-head matchup analysis between players or teams

## Domain Config: `COMPETITIVE_SPORTS`
- tool_tags: `{"sports", "literature"}`
- valid_domain_categories: `("competitive_sports", "basketball", "soccer", "football", "baseball", "tennis")`
- hypothesis_types: `("performance", "tactical", "statistical", "predictive")`
- score_definitions: performance_score, statistical_significance, sample_size
- identifier_type: `"player"` or `"team"`

## Visualization
- [ ] `render_player_radar` -- radar chart comparing player attributes (Recharts)
- [ ] `render_season_timeline` -- performance trends over a season (Recharts)
- [ ] `render_shot_chart` -- spatial shot/play visualization (Custom SVG, basketball/soccer)

## Cross-Domain Potential
- Sports + Training: "What training protocols produce the best NBA pre-season conditioning results?"
- Sports + Nutrition: "What supplements do elite soccer players use and what's the evidence?"
- Sports + Molecular: "What are the pharmacological mechanisms behind caffeine's effect on sprint performance?"

---

# Additional Domains -- BACKLOG

The engine is domain-agnostic via `DomainConfig` + `DomainRegistry`. Adding a new domain requires zero changes to existing code (see `CONTRIBUTING.md`). Potential future domains:

- [ ] Genomics / bioinformatics (variant interpretation, gene expression analysis)
- [ ] Environmental science (pollutant fate, ecosystem modeling)
- [ ] Materials science (property prediction, synthesis planning)
- [ ] Clinical pharmacology (drug interactions, pharmacokinetics)

For molecular science specifically:
- [ ] Expanded organism coverage (E. coli, P. aeruginosa, A. baumannii, M. tuberculosis)
- [ ] Per-organism resistance knowledge base with literature references
- [ ] Organism-aware prompt guidance (Gram-neg vs mycobacteria screening strategies)

---

# Phase 11: Investigation Comparison -- BACKLOG

Side-by-side comparison of investigation runs for reproducibility and consensus analysis.

## 11A. Comparison Domain
- [ ] `Comparison` entity: list of investigation IDs, consensus candidates, overlap metrics
- [ ] Candidate overlap calculation (by identifier + domain-specific similarity)
- [ ] Finding overlap detection (by hypothesis + title similarity)
- [ ] Score aggregation across runs (mean, std, min, max)

## 11B. Comparison API
- [ ] `POST /compare` -- accept list of investigation IDs, return comparison
- [ ] `GET /compare/{id}` -- retrieve saved comparison

## 11C. Comparison Console
- [ ] `/compare` page: pick 2+ completed investigations
- [ ] Side-by-side candidate table with overlap highlighting
- [ ] Consensus candidates panel (appear in N/M runs)
- [ ] Score distribution visualization (per candidate across runs)
- [ ] Findings diff view (shared vs unique per run)

**Verification:** Compare 2 completed investigations, verify overlap metrics and consensus candidates render correctly.

---

# ~~MCP Server~~ -- REJECTED

Exposing Ehrlich's 84 tools as an MCP server was considered and rejected. The tools alone (ChEMBL queries, RDKit computations, etc.) are commodity API wrappers -- the value is the multi-model orchestration (Director-Worker-Summarizer), hypothesis-driven methodology, and parallel experiment execution. An MCP client consuming Ehrlich's tools would lose the scientific rigor that the orchestration guarantees.

Ehrlich remains an MCP **consumer** via `MCPBridge` (connecting to external servers like Excalidraw), which adds value by extending the Researcher's toolkit.

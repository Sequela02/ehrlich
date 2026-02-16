# Ehrlich Roadmap

Hackathon: Feb 10-16, 2026. Phases 0-14 delivered during hackathon. Post-hackathon focus: engagement depth, monetization, collaboration.

## Phases

| Phase | Status | File |
|-------|--------|------|
| Phase 0: Infrastructure | DONE | [phase-00-infrastructure.md](phase-00-infrastructure.md) |
| Phase 1: Chemistry Context | DONE | [phase-01-chemistry.md](phase-01-chemistry.md) |
| Phase 2: Literature + Analysis | DONE | [phase-02-literature-analysis.md](phase-02-literature-analysis.md) |
| Phase 3: Prediction Context | DONE | [phase-03-prediction.md](phase-03-prediction.md) |
| Phase 4: Simulation Context | DONE | [phase-04-simulation.md](phase-04-simulation.md) |
| Phase 5: Investigation Agent | DONE | [phase-05-investigation-agent.md](phase-05-investigation-agent.md) |
| Phase 6: Console Integration | DONE | [phase-06-console.md](phase-06-console.md) |
| Phase 7: Integration + Demo | DONE | [phase-07-integration-demo.md](phase-07-integration-demo.md) |
| Phase 8: Multi-Model Architecture + Polish | DONE | [phase-08-multi-model.md](phase-08-multi-model.md) |
| Phase 9: Molecule Visualization Suite | DONE | [phase-09-molecule-visualization.md](phase-09-molecule-visualization.md) |
| Phase 10A: Hypothesis-Driven Investigation Engine | DONE | [phase-10a-hypothesis-engine.md](phase-10a-hypothesis-engine.md) |
| Phase 10B: Domain-Agnostic Generalization | DONE | [phase-10b-domain-agnostic.md](phase-10b-domain-agnostic.md) |
| Phase 10C: Claude SDK Optimization | DONE | [phase-10c-sdk-optimization.md](phase-10c-sdk-optimization.md) |
| Phase 10D: Landing Site (web/) | DONE | [phase-10d-landing-site.md](phase-10d-landing-site.md) |
| Phase 10E: Training Science Enhancement | DONE | [phase-10e-training-enhancement.md](phase-10e-training-enhancement.md) |
| Phase 10F: Nutrition Science Enhancement | DONE | [phase-10f-nutrition-enhancement.md](phase-10f-nutrition-enhancement.md) |
| Phase 11: Investigation Comparison | DONE | [backlog.md](backlog.md) |
| Phase 12: Platform Infrastructure | DONE | [phase-12-platform-infrastructure.md](phase-12-platform-infrastructure.md) |
| Phase 13: Impact Evaluation Domain | DONE | [phase-13-impact-evaluation.md](phase-13-impact-evaluation.md) |
| Phase 14: Scientific Engine Hardening | DONE | [phase-14-engine-hardening.md](phase-14-engine-hardening.md) |
| Phase 15: Stripe + Free Tier | TODO | [backlog.md](backlog.md) |
| Phase 16: Interactive Investigations | TODO | [backlog.md](backlog.md) |
| Phase 17: Validation & Benchmarking | TODO | [backlog.md](backlog.md) |
| Phase 18: Investigation Organization | TODO | [backlog.md](backlog.md) |
| Phase 19: Collaboration | TODO | [backlog.md](backlog.md) |
| Phase 20: Operations & Observability | TODO | [backlog.md](backlog.md) |
| Phase 21: Agent Architecture Evolution | TODO | [backlog.md](backlog.md) |
| Phase 22: MCP Bridge Self-Service | TODO | [backlog.md](backlog.md) |
| Phase 23: Competitive Sports Domain | TODO | [backlog.md](backlog.md) |
| Phase 24: Multi-Provider Support (BYOP) | TODO | [backlog.md](backlog.md) |
| Phase 25: Additional Data Sources | TODO | [backlog.md](backlog.md) |
| Phase 26+: Future Domains | BACKLOG | [backlog.md](backlog.md) |

## Dependency Graph

```
Phase 0 (Infrastructure) -- DONE
    |
Phase 1 (Chemistry) -- DONE
    |         \
Phase 2A-C    Phase 2D-E
(Literature)  (Analysis)  -- DONE
    |              |
    +----- + ------+
           |
     Phase 3 (Prediction) -- DONE
           |
     Phase 4 (Simulation) -- DONE
           |
     Phase 5 (Agent Loop) -- DONE
           |
     Phase 6 (Console) -- DONE
           |
     Phase 7 (Integration + Demo) -- DONE
           |
     Phase 8 (Multi-Model + Polish) -- DONE
           |
     Phase 9 (Molecule Visualization) -- DONE
           |
     Phase 10A (Hypothesis-Driven Engine) -- DONE
           |
     Scientific Methodology Upgrade (cross-cutting) -- All 6 Phases DONE
           |
     Domain-Agnostic Generalization -- DONE
           |
     Multi-Domain Investigations -- DONE
           |
     Self-Referential Research -- DONE
           |
     Shared Context + MCP Bridge + Training/Nutrition APIs -- DONE
           |
     Domain-Specific Visualization System -- DONE
           |
     Claude SDK Optimization -- DONE
           |
     Landing Site (web/) -- DONE + DEPLOYED (Vercel)
           |
     ┌─────┼──────────────┐
     │     │              │
Training  Nutrition   Competitive
Enhancement Enhancement  Sports
  (DONE)    (DONE)     Domain (Phase 23)
     │     │
     └─────┘
           |
     Phase 12: Platform Infrastructure -- DONE
     (PostgreSQL + WorkOS Auth + BYOK + Credits)
           |
     Phase 13: Impact Evaluation Domain -- DONE
     (Causal inference + Document upload + MX/US APIs)
     13A -> 13B -> 13A-2 -> 13D -> 13C (all DONE)
           |
     Phase 14: Scientific Engine Hardening -- DONE
     14A-14J DONE ── 14G (Validation Runs) -> Phase 17
           |
     ══════════════════════════════════════
     POST-HACKATHON (Feb 16, 2026 onwards)
     ══════════════════════════════════════
           |
     ┌─────┴─────┐
     │           │
Phase 15      Phase 16
(Stripe)      (Interactive)
     │        16A | 16B | 16C
     └─────┬─────┘
           |
     Phase 17: Validation & Benchmarking
     (includes 14G validation runs)
           |
     Phase 18: Investigation Organization
     18A (Projects) -> 18B (Tags) -> 18C (Search)
           |
     Phase 19: Collaboration
     19A (Shared Links) -> 19B (Teams) -> 19C (Comments) -> 19D (Collaborative Steering)
           |
     Phase 20: Operations & Observability
     (Admin dashboard, Sentry, analytics, rewarded ads)
           |
     Phase 21: Agent Architecture Evolution
     (Planner + Reviewer agents, Bayesian surprise)
           |
     Phase 22: MCP Bridge Self-Service
     (User MCP registration, auto-discovery)
           |
     Phase 23: Competitive Sports Domain
     (NBA, football-data.org, ESPN)
           |
     Phase 24: Multi-Provider Support (BYOP)
     (OpenAI + Google adapters)
           |
     Phase 25: Additional Data Sources
     (OECD, INEGI DENUE, EPA Envirofacts)
           |
     Phase 26+: Future Domains
     (Genomics, Environmental, Materials, Clinical Pharma)
```

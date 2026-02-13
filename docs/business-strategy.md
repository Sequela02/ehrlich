# Ehrlich Business Strategy

> Public strategy document. Ehrlich is AGPL-3.0 open source.
> For technical implementation, see [roadmap.md](roadmap.md) Phase 12.

## Market Position

Ehrlich sits between AI wrappers and enterprise platforms.

### What Ehrlich Is Not
- Not a wrapper (wrappers: prompt -> LLM -> response -> display)
- Not a chatbot with a science skin

### What Ehrlich Is
- A domain-agnostic scientific reasoning engine
- 65 real tools with real computation (RDKit, XGBoost, molecular docking)
- 15 external data sources (ChEMBL, PubChem, RCSB PDB, UniProt, ClinicalTrials.gov, PubMed, wger, NIH DSLD, USDA FoodData, OpenFDA, EPA CompTox, Semantic Scholar, Open Targets, GtoPdb, RxNav) + 1 internal (FTS5)
- Multi-model orchestration (Director-Worker-Summarizer)
- Scientific methodology grounded in Popper, Fisher, GRADE, Bayesian frameworks
- The AI is the scientist using the lab -- not the lab itself

### The Gap
- Wrappers (Elicit, Consensus, Perplexity): search + summarize, no computation, no methodology, ~$0 per query
- Enterprise platforms (Schrodinger, Recursion): full stack, $100K+/year, single domain
- Ehrlich: multi-domain scientific engine, $2-10 per investigation, accessible to students and pharma alike

## Pricing Model

### Universal Credits
One currency. User decides quality per investigation.

| Investigation Tier | Director Model | Credits | API Cost Range |
|-------------------|----------------|---------|----------------|
| Haiku | Haiku 4.5 | 1 | Low |
| Sonnet | Sonnet 4.5 | 3 | Medium |
| Opus | Opus 4.6 | 5 | Higher |

Researcher is always Sonnet 4.5 (tool execution). Summarizer is always Haiku 4.5 (compression). The Director model determines investigation quality -- hypothesis depth, experimental design rigor, synthesis nuance.

### Credit Packs

| Pack | Credits | Discount |
|------|---------|----------|
| Starter (5) | 5 | -- |
| Researcher (25) | 25 | 20% |
| Lab (50) | 50 | 30% |
| Monthly (30/mo) | 30 auto-refill | 33% |

Monthly subscription = auto-refilling credit pack at a discount. Not a separate product. Credits expire after 60 days (prevents hoarding, encourages usage).

### Why Per-Investigation, Not Per-Token
An investigation is a complete scientific workflow: literature survey, hypothesis formulation, experiment execution, evaluation, synthesis. That's an outcome with a deliverable (the report), not a token count. Pricing the outcome aligns cost with value.

**Research backing:** Chargebee 2026 AI Agent Pricing Playbook, Bessemer AI Pricing Playbook, BCG Rethinking B2B Software Pricing, Simon-Kucher Value-Based Pricing in the Age of AI.

## Tier Structure

### Free Tier (Accessible to Everyone)
- 3 Haiku investigations per month
- Full 6-phase scientific methodology
- All 65 tools, all 15 data sources
- Full audit trail and report
- No feature gates -- same product, different model quality

**Philosophy:** Ehrlich should be accessible to students, academics, and casual researchers. The free tier is not a loss leader -- it's the product working as intended at a lower reasoning depth.

### Ad-Funded Bonus Credits
- Optional: watch an ad to earn 1 additional Haiku credit
- Ads are clearly separated from investigation results
- Ads never influence scientific output
- Target audience (researchers, scientists) commands premium B2B CPMs
- This is a supplementary mechanism, not a primary revenue stream

### Scientific Funnel (Free Feeds Paid)
Ehrlich's self-referential research (FTS5) means free Haiku investigations produce real indexed findings. A subsequent paid Opus investigation can query those prior findings via `search_prior_research`, making the paid investigation better because it has more context.

```
3 free Haiku investigations -> findings indexed in FTS5
1 paid Opus investigation -> queries prior findings -> deeper, better results
```

Free investigations are groundwork, not waste.

### Credit Packs (Pay-as-you-go)
Buy credits when needed. No commitment. Best for students, occasional users.

### Monthly Plan
30 credits/month at 33% discount. Auto-refill. Best for active researchers with ongoing projects.

### Enterprise
- BYOK (Bring Your Own Key) -- use your own Anthropic API key
- Platform fee for 65 tools, 15 data sources, methodology engine
- Commercial license (AGPL exemption) for private modifications
- Future: BYOP (Bring Your Own Provider) -- multi-provider support

## Accessibility Strategy

### Core Principle
The product is the same for a student in Mexico and a pharma company in Boston. The model quality is the only variable. No feature gates between tiers.

### Who Uses What

| User | Typical Behavior |
|------|-----------------|
| Student | Free Haiku + ad bonus. Occasional 5-pack before deadlines |
| Academic researcher | Monthly 30 credits. Sonnet for routine, Opus for publications |
| Casual explorer | Free Haiku only |
| Power user | Monthly + extra packs. Heavy Opus |
| Enterprise / Pharma | BYOK + commercial license |

### Why Not Charge Everyone
- Science should be accessible
- Free users generate FTS5 findings that improve the platform for everyone
- Free-to-paid conversion validated at 3-5% base, 8-15% top quartile (First Page Sage 2026)
- The quality difference between Haiku and Opus is the conversion mechanism -- users experience it firsthand

## AGPL-3.0 Dual Licensing

### Why AGPL
AGPL-3.0 closes the "ASP loophole": if someone runs modified Ehrlich as a network service, they must publish all source code. This prevents cloud providers from offering Ehrlich-as-a-Service without contributing back.

### Dual Licensing Model
- **Open source (AGPL):** Anyone can use, modify, self-host. Modifications must be shared if offered as a service.
- **Commercial license:** Companies that want private modifications pay for an AGPL exemption. This is the enterprise revenue mechanism.

### Precedent
MongoDB, Confluent (51% YoY growth with dual licensing), GitLab, Spree Commerce all use this model successfully.

### What This Means for Users
- Individuals, students, academics: use freely under AGPL. No restrictions.
- Companies self-hosting internally: use freely under AGPL (no network distribution).
- Companies offering Ehrlich as a service: must open-source modifications OR purchase commercial license.

## Post-Validation Roadmap

These items are sequenced after product-market fit is validated:

### Multi-Provider Support (BYOP)
Abstract `AnthropicClientAdapter` into a generic `LLMClient` interface. Add OpenAI and Google as Researcher/Summarizer options first (low risk). Non-Claude Directors only after quality validation.

### Model Selection Per Role
Enterprise users can configure which model handles each role:
- Director: Opus 4.6, o3, Gemini 2.5 Pro
- Researcher: Sonnet 4.5, GPT-4o, Gemini Flash
- Summarizer: Haiku 4.5, GPT-4o-mini, Gemini Flash

### Additional Domains
The `DomainConfig` + `DomainRegistry` system supports any scientific domain. Planned:
- Competitive Sports (game statistics, player analytics)
- Genomics / Bioinformatics
- Environmental Science
- Materials Science

### Cost Transparency (PostHog Model)
Radical cost transparency -- users see token breakdown by model, cache savings, total API cost. Open source codebase means pricing math is already visible. Embrace it as a differentiator.

## Research Sources

Strategy validated against tier-1 sources:

- [Bessemer Venture Partners - AI Pricing Playbook](https://www.bvp.com/atlas/the-ai-pricing-and-monetization-playbook)
- [BCG - Rethinking B2B Software Pricing in the Era of AI](https://www.bcg.com/publications/2025/rethinking-b2b-software-pricing-in-the-era-of-ai)
- [Simon-Kucher - Value-Based Pricing in the Age of AI](https://www.simon-kucher.com/en/insights/price-model-shifts-age-ai)
- [Chargebee - 2026 AI Agent Pricing Playbook](https://www.chargebee.com/blog/pricing-ai-agents-playbook/)
- [Chargebee - How Intercom Built Outcome-Based Pricing](https://blog.chargebee.com/blog/how-intercom-built-its-outcome-based-pricing-model-for-ai/)
- [Growth Unhinged - AI Agent Pricing Framework](https://www.growthunhinged.com/p/ai-agent-pricing-framework)
- [First Page Sage - Freemium Conversion Rates 2026](https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/)
- [First Page Sage - Free Trial Conversion Benchmarks](https://firstpagesage.com/seo-blog/saas-free-trial-conversion-rate-benchmarks/)
- [Open Core Ventures - AGPL License](https://www.opencoreventures.com/blog/agpl-license-is-a-non-starter-for-most-companies)
- [Monetizely - Dual Licensing Strategy](https://www.getmonetizely.com/articles/should-your-saas-company-adopt-a-dual-licensing-strategy)
- [Spree Commerce - AGPL-3.0 + Commercial License](https://spreecommerce.org/why-spree-is-changing-its-open-source-license-to-agpl-3-0-and-introducing-a-commercial-license/)

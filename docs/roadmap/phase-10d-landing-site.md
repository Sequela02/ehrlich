Back to [Roadmap Index](README.md)

# Phase 10D: Landing Site (`web/`) -- DONE

Separate TanStack Start project for the public-facing landing page. SSR/SSG for SEO, same React + TypeScript + Bun stack as console, independent build and deployment.

## Why Separate from Console

- **Different concerns**: landing page is marketing/SEO content; console is the authenticated SPA
- **Different optimization**: SSR/SSG with zero-JS static pages vs client-side SPA with heavy WebGL/charting
- **Independent deployment**: CDN-friendly static output vs API-connected app server
- **Clean separation**: no marketing code in the investigation UI, no app dependencies in the landing page

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | TanStack Start | Same TanStack ecosystem as console, SSR/SSG built-in, Nitro server |
| Runtime | Bun | Same as console |
| Styling | Tailwind CSS 4 | Same as console, shared design tokens (OKLCH) |
| Fonts | Space Grotesk + JetBrains Mono | Same as console (Lab Protocol identity) |
| Icons | Lucide React | Same as console |
| Build | Vite 7 (via Nitro) | Same toolchain |

## Project Structure

```
web/
├── src/
│   ├── routes/
│   │   ├── __root.tsx            # Root layout (shell, SEO meta, font loading)
│   │   └── index.tsx             # Landing page (all sections wired)
│   ├── components/
│   │   ├── Nav.tsx               # Fixed navbar with scroll progress bar + mobile menu
│   │   ├── Footer.tsx            # Minimal footer (links, license, year)
│   │   ├── SectionHeader.tsx     # Mono label with left border accent
│   │   ├── Hero.tsx              # Bottom-third hero with MolecularNetwork, stats badges, CTAs
│   │   ├── MolecularNetwork.tsx  # 3D rotating node graph (Canvas 2D, mouse repulsion, CSS mask)
│   │   ├── HowItWorks.tsx        # 6-phase methodology timeline with vertical line
│   │   ├── ConsolePreview.tsx    # Browser-frame mockups (timeline, hypotheses, candidates)
│   │   ├── Architecture.tsx      # Director-Worker-Summarizer model cards, dot grid bg
│   │   ├── Domains.tsx           # 3 domain cards with tool counts + multi-domain callout
│   │   ├── Visualizations.tsx    # 4 visualization category cards
│   │   ├── DataSources.tsx       # 16 source cards with teal glow
│   │   ├── WhoItsFor.tsx         # 3 persona cards (Student, Academic, Industry)
│   │   ├── Differentiators.tsx   # 3 differentiator cards with capabilities
│   │   ├── OpenSource.tsx        # Code snippet + licensing section
│   │   ├── Roadmap.tsx           # Planned domains + platform features
│   │   └── CTA.tsx               # Pricing tiers, terminal quickstart, primary glow
│   ├── styles/
│   │   └── app.css               # Tailwind 4 entry + OKLCH tokens + animations
│   ├── lib/
│   │   ├── constants.ts          # Stats, links, domain data, methodology phases
│   │   ├── use-reveal.ts         # IntersectionObserver scroll reveal hook
│   │   └── use-scroll-progress.ts # Scroll progress fraction hook
│   ├── router.tsx                # TanStack Router factory (getRouter)
│   └── routeTree.gen.ts          # Auto-generated route tree
├── public/
│   └── favicon.svg               # Green "E" favicon
├── package.json                  # ehrlich-web, Bun scripts
├── vite.config.ts                # TanStack Start + Nitro + Tailwind
└── tsconfig.json                 # src/ paths, strict mode
```

## WEB-1: Project Scaffolding -- DONE

- [x] TanStack Start project in `web/` with Bun
- [x] `vite.config.ts` with tanstackStart + nitro + tailwindcss + viteReact + tsConfigPaths
- [x] Tailwind CSS 4 with OKLCH design tokens matching console's Lab Protocol identity
- [x] Space Grotesk + JetBrains Mono font loading via Google Fonts
- [x] Root layout with `shellComponent`, `HeadContent`, CSS `?url` import
- [x] Favicon + meta tags (title, description, OG, Twitter card, theme-color)
- [x] `bun run build` produces `.output/` (client + SSR + Nitro server)
- [x] `bun run typecheck` -- zero errors

## WEB-2: Landing Page Sections -- DONE

- [x] **Hero**: bottom-third placement, MolecularNetwork 3D canvas (CSS mask edge fade), stats badges, CTA buttons
- [x] **HowItWorks**: 6-phase methodology timeline with vertical connecting line, hypothesis/experiment structure callouts
- [x] **ConsolePreview**: browser-frame mockups (investigation timeline, hypothesis board, candidate table, ADMET radar)
- [x] **Architecture**: Director-Worker-Summarizer model cards with data pipes, dot grid bg, amber radial glow
- [x] **Domains**: 3 domain cards with tool counts, multi-domain callout, extensibility card
- [x] **Visualizations**: 4 visualization category cards with tech labels, extensibility callout
- [x] **DataSources**: 16 source cards (2-col grid), surface bg with teal radial glow, self-referential research callout
- [x] **WhoItsFor**: 3 persona cards (Student, Academic, Industry)
- [x] **Differentiators**: 3 differentiator cards with capabilities lists
- [x] **OpenSource**: code snippet + dual licensing (AGPL-3.0 + Commercial), GitHub link
- [x] **Roadmap**: planned domains (3 cards) + platform features (dashed border cards)
- [x] **CTA**: pricing tiers (4 cards), terminal quickstart with copy, primary radial glow

## WEB-3: Navigation + Footer + Meta -- DONE

- [x] **Nav**: fixed top bar, scroll progress indicator, desktop links, mobile hamburger menu
- [x] **Footer**: AGPL-3.0 branding, mapped footer links, responsive layout
- [x] **SectionHeader**: mono label with left border accent (reused across sections)
- [x] **SEO meta**: full OG tags, Twitter card, theme-color, description
- [x] **Smooth scroll**: anchor links (`#architecture`, `#methodology`, `#domains`, `#data-sources`)
- [x] Responsive: mobile hamburger nav, stacked sections

## WEB-5: Visual Polish + Animations -- DONE

- [x] Motion scroll-triggered reveals (whileInView, once: true)
- [x] Staggered children animation (80-120ms delay cascade)
- [x] Architecture data pipe animation (flowing dots between model tiers)
- [x] Domain/differentiator/persona card hover effects (border-primary, y-shift)
- [x] MolecularNetwork 3D canvas: 90 nodes, mouse repulsion, shimmer connections, CSS mask edge fade
- [x] Section zoning: alternating bg-surface/30 + strategic radial glows (amber/teal/primary)
- [x] CSS dot grid on Architecture (32px, static, graph-paper aesthetic)
- [x] Scroll progress bar in navbar
- [x] WCAG AA color contrast (muted-foreground 0.60, secondary 0.60, min /60 opacity)
- [x] Sequential heading hierarchy (h1 -> h2 -> h3, no skips)
- [x] Font preloading for Google Fonts (preload + stylesheet)
- [x] All OKLCH tokens (zero hardcoded gray-* classes)
- [x] Lighthouse: Performance 67, Accessibility 95, Best Practices 100, SEO 100

## Verification

- [x] `cd web && bun run build` -- zero errors
- [x] `cd web && bun run typecheck` -- zero TypeScript errors
- [x] Visual: Lab Protocol identity consistent with console (OKLCH tokens, fonts, dark theme)
- [x] All docs updated: `CLAUDE.md`, `README.md`, `docs/architecture.md`, `docs/roadmap.md`

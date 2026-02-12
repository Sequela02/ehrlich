import { ArrowRight } from "lucide-react";
import { useReveal } from "@/lib/use-reveal";
import { STATS } from "@/lib/constants";
import { HERO_ASCII } from "@/lib/ascii-patterns";

export function Hero() {
  const revealRef = useReveal();

  return (
    <section className="min-h-screen relative flex flex-col justify-end pb-20 pt-32 px-4 lg:px-0 max-w-[1200px] mx-auto border-l border-r border-border/30">
      <div className="ascii-bg">
        <pre>{HERO_ASCII}</pre>
      </div>

      <div ref={revealRef} className="reveal-section w-full lg:w-3/4">
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-primary/80 mb-2 block">
          Open Source &middot; AGPL-3.0
        </span>

        <h1 className="text-6xl md:text-8xl font-bold tracking-tighter text-foreground mb-4">
          Ehrlich
        </h1>

        <h2 className="text-xl md:text-2xl text-foreground/80 font-normal mb-8">
          AI-Powered Scientific Discovery Engine
        </h2>

        <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed mb-12">
          Hypothesis-driven research across molecular science, training science,
          and nutrition — powered by Claude.
        </p>

        <div className="flex flex-wrap items-center gap-4 mb-16">
          <a
            href="/console"
            className="bg-primary text-primary-foreground hover:opacity-90 transition-colors font-medium text-sm px-6 py-3 rounded-sm flex items-center gap-2 group"
          >
            Launch Console
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </a>
          <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-wide">
            No account required &middot; runs locally
          </span>
          <a
            href="https://github.com"
            className="border border-border text-foreground hover:border-primary hover:text-primary transition-colors font-medium text-sm px-6 py-3 rounded-sm"
          >
            View on GitHub
          </a>
        </div>

        <div className="border-t border-border pt-6 flex flex-wrap gap-8 font-mono text-[11px] text-muted-foreground uppercase tracking-[0.12em]">
          <span>
            <span className="text-primary">{STATS.tools}</span> tools
          </span>
          <span>
            <span className="text-primary">{STATS.dataSources}</span> data sources
          </span>
          <span>
            <span className="text-primary">{STATS.domains}</span> domains
          </span>
          <span>
            <span className="text-primary">{STATS.models}</span> models
          </span>
        </div>
      </div>
    </section>
  );
}

import { useRef } from "react";
import { ArrowRight } from "lucide-react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { STATS } from "@/lib/constants";
import { AsciiTorus } from "./AsciiTorus";

export function Hero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true });
  const reduced = useReducedMotion();

  return (
    <section ref={containerRef} className="min-h-[85vh] relative flex items-end overflow-hidden">
      {/* Subtle gradient accent */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-primary/5 rounded-full blur-[120px]" />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-[1200px] mx-auto px-4 lg:px-0 pb-24 pt-32 grid lg:grid-cols-2 gap-12 lg:gap-16 items-end">

        {/* Left: Value Proposition */}
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex flex-col gap-8"
        >
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter leading-[0.9] text-foreground">
            Scientific<br />
            methodology,<br />
            <span className="text-primary">automated.</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground/80 max-w-2xl leading-relaxed">
            Formulate falsifiable hypotheses. Design controlled experiments. Test against
            {" "}{STATS.dataSources} real databases. Grade the evidence. {STATS.tools} computational
            tools across {STATS.domains} scientific domains. Grounded in Popper, Fisher, and GRADE.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-[11px] text-primary border border-primary/20 bg-primary/5 px-2.5 py-1 rounded">
              {STATS.tools} tools
            </span>
            <span className="font-mono text-[11px] text-secondary border border-secondary/20 bg-secondary/5 px-2.5 py-1 rounded">
              {STATS.dataSources} data sources
            </span>
            <span className="font-mono text-[11px] text-accent border border-accent/20 bg-accent/5 px-2.5 py-1 rounded">
              {STATS.domains} domains
            </span>
            <span className="font-mono text-[11px] text-muted-foreground border border-border px-2.5 py-1 rounded">
              {STATS.vizTools} visualizations
            </span>
          </div>

          <div className="flex flex-wrap gap-4 pt-2">
            <a
              href="/console"
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground font-medium text-sm px-6 py-3 rounded-sm hover:opacity-90 transition-opacity"
            >
              Start Free
              <ArrowRight size={14} />
            </a>
            <a
              href="https://github.com/sequelcore/ehrlich"
              className="inline-flex items-center gap-2 border border-border text-foreground font-medium text-sm px-6 py-3 rounded-sm hover:border-primary hover:text-primary transition-colors"
            >
              View on GitHub
            </a>
          </div>
        </motion.div>

        {/* Right: ASCII 3D Torus */}
        <motion.div
          initial={reduced ? false : { opacity: 0, scale: 0.95 }}
          animate={isInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
          className="hidden lg:flex items-center justify-center"
        >
          <AsciiTorus />
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-background to-transparent z-10" />
    </section>
  );
}

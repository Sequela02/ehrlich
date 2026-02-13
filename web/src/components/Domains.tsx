import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { DOMAINS } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function Domains() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();

  return (
    <section id="domains" className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <SectionHeader title="Scientific Domains" />

      <div className="mb-10 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Three domains. Domain-agnostic engine.
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          Each domain brings its own tools, scoring definitions, and prompt examples.
          The orchestrator, methodology, and persistence work identically across all.
          Multi-domain questions are auto-detected and merged.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial={reduced ? false : "hidden"}
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="space-y-6"
      >
        {DOMAINS.map((domain) => (
          <motion.div
            key={domain.label}
            variants={cardVariants}
            className="bg-surface border border-border rounded-sm p-6 lg:p-8 hover:border-primary/40 transition-colors group"
          >
            <div className="flex flex-col lg:flex-row lg:gap-8">
              {/* Header */}
              <div className="lg:w-64 shrink-0 mb-4 lg:mb-0">
                <div className="flex items-center justify-between lg:flex-col lg:items-start lg:gap-2">
                  <h4 className="font-mono text-sm tracking-[0.12em] uppercase text-foreground group-hover:text-primary transition-colors">
                    {domain.label}
                  </h4>
                  <span className="font-mono text-[10px] text-primary border border-primary/20 bg-primary/5 px-2 py-1 rounded-[1px]">
                    {domain.toolCount} TOOLS
                  </span>
                </div>
                <p className="text-sm text-muted-foreground/70 mt-2 leading-relaxed">
                  {domain.description}
                </p>
              </div>

              {/* Capabilities */}
              <div className="flex-1 grid md:grid-cols-2 gap-x-6 gap-y-1.5">
                {domain.capabilities.map((cap) => (
                  <div
                    key={cap}
                    className="font-mono text-[11px] text-muted-foreground flex items-start gap-2"
                  >
                    <span className="text-primary mt-0.5 shrink-0">&bull;</span>
                    {cap}
                  </div>
                ))}
              </div>

              {/* Viz tools */}
              <div className="lg:w-44 shrink-0 mt-4 lg:mt-0">
                <span className="font-mono text-[10px] text-muted-foreground/50 uppercase block mb-2">
                  Visualizations
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {domain.vizTools.map((viz) => (
                    <span
                      key={viz}
                      className="font-mono text-[10px] text-secondary/70 border border-secondary/20 bg-secondary/5 px-1.5 py-0.5 rounded"
                    >
                      {viz}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Example prompt */}
            <div className="mt-4 pt-4 border-t border-border/30">
              <div className="bg-background border border-border/50 p-3 rounded-sm">
                <span className="font-mono text-[9px] text-muted-foreground/40 mb-1 select-none block uppercase">
                  Example:
                </span>
                <code className="font-mono text-[11px] text-muted-foreground">
                  {domain.prompt}
                </code>
              </div>
            </div>
          </motion.div>
        ))}

        {/* Multi-domain callout */}
        <motion.div
          variants={cardVariants}
          className="bg-primary/5 border border-primary/20 rounded-sm p-6 lg:p-8"
        >
          <div className="flex flex-col md:flex-row md:items-start gap-6">
            <div className="flex-1">
              <h4 className="font-mono text-sm tracking-[0.08em] uppercase text-primary mb-2">
                Multi-Domain Investigations
              </h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Ask a question that spans multiple domains and Ehrlich detects it automatically.{" "}
                <code className="font-mono text-[10px] text-primary">DomainRegistry.detect()</code>{" "}
                returns all matching domains.{" "}
                <code className="font-mono text-[10px] text-primary">merge_domain_configs()</code>{" "}
                creates a synthetic config with the union of tool tags, concatenated scoring definitions,
                and joined prompt examples. The researcher sees tools from all relevant domains.
              </p>
            </div>
            <div className="shrink-0 font-mono text-[11px] text-muted-foreground/60 leading-relaxed md:max-w-xs">
              <span className="text-foreground/50 block mb-1">Example:</span>
              &ldquo;Evaluate creatine supplementation for resistance training performance
              and renal safety&rdquo;
              <span className="block mt-1 text-primary/60">
                &rarr; Nutrition + Training domains merged
              </span>
            </div>
          </div>
        </motion.div>

        {/* Extensibility card */}
        <motion.div
          variants={cardVariants}
          className="bg-transparent border border-dashed border-border/50 rounded-sm p-6 lg:p-8 hover:border-primary/50 transition-colors"
        >
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="flex-1">
              <h4 className="font-mono text-sm tracking-[0.12em] uppercase text-muted-foreground/60 mb-2">
                Add Your Domain
              </h4>
              <p className="text-sm text-muted-foreground/60 max-w-lg leading-relaxed">
                Register a{" "}
                <code className="font-mono text-xs text-primary/60">DomainConfig</code>{" "}
                with tool tags, data sources, scoring definitions, and prompt examples.
                The engine handles orchestration, persistence, visualization, and reporting.
                Connect external tools via MCP servers &mdash; community-built domains plug
                in without modifying the core engine.
              </p>
            </div>
            <a
              href="https://github.com/sequelcore/ehrlich/blob/main/CONTRIBUTING.md"
              className="font-mono text-xs text-primary border border-primary/30 bg-primary/5 px-4 py-2 rounded hover:bg-primary/10 transition-colors shrink-0"
            >
              Contributing Guide
            </a>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}

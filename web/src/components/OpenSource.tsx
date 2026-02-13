import { useRef } from "react";
import { Github } from "lucide-react";
import { motion, useInView, useReducedMotion } from "motion/react";

const CODE_SNIPPET = `MATERIALS_SCIENCE = DomainConfig(
    name="Materials Science",
    tool_tags=frozenset({"materials", "simulation"}),
    score_definitions=[
        ScoreDefinition(
            name="hardness",
            label="Vickers Hardness",
            unit="HV",
        ),
    ],
    prompt_examples=[
        "Discover alloys with high-temperature stability..."
    ],
)

registry.register(MATERIALS_SCIENCE)`;

export function OpenSource() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();

  return (
    <section className="py-32 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <motion.div
        ref={ref}
        initial={reduced ? false : { opacity: 0, y: 24 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="flex flex-col items-start"
      >
        <h2 className="text-5xl md:text-7xl font-bold tracking-tight text-foreground mb-6">
          <span className="text-primary">Open</span> Source
        </h2>

        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mb-16 leading-relaxed font-light">
          AGPL-3.0 licensed. Built in public. Anyone can extend Ehrlich with
          new scientific domains &mdash; materials science, environmental
          research, clinical medicine, or anything else.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 w-full mb-16">
          {/* Code snippet */}
          <div className="terminal-frame">
            <div className="terminal-header">
              <span className="terminal-dot" />
              <span className="terminal-dot" />
              <span className="terminal-dot" />
              <span className="ml-3 font-mono text-[10px] text-muted-foreground/50 uppercase tracking-wider">
                domain_config.py
              </span>
            </div>
            <div className="p-5">
              <pre className="font-mono text-[11px] text-muted-foreground leading-relaxed whitespace-pre overflow-x-auto">
                <code>{CODE_SNIPPET}</code>
              </pre>
            </div>
          </div>

          {/* Feature list */}
          <div className="flex flex-col justify-center gap-8">
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                Add a Domain
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Zero changes to existing code. Define a{" "}
                <code className="font-mono text-xs text-primary">
                  DomainConfig
                </code>
                , register your tools, and the engine handles orchestration,
                persistence, and reporting.
              </p>
            </div>
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                65 Tools Across 3 Domains
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Chemistry, literature, analysis, prediction, simulation,
                training, nutrition, and visualization. Each tagged with domain
                metadata for automatic filtering.
              </p>
            </div>
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                Domain-Agnostic Engine
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                The orchestrator, persistence layer, and reporting system work
                identically across all domains. Your tools are the only
                domain-specific code.
              </p>
            </div>
          </div>
        </div>

        <a
          href="https://github.com/sequelcore/ehrlich"
          className="font-mono text-sm text-foreground/80 hover:text-primary border border-border bg-surface px-4 py-2 rounded-sm flex items-center gap-3 transition-colors group"
        >
          <Github size={16} />
          github.com/sequelcore/ehrlich
        </a>
      </motion.div>
    </section>
  );
}

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
          AGPL-3.0 dual licensed. Use it free for research and teaching.
          Purchase a commercial license for private modifications.
          Self-host, extend, contribute.
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

          {/* Licensing + features */}
          <div className="flex flex-col justify-center gap-8">
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                AGPL-3.0 (Free Use)
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Students, academics, and individual researchers use Ehrlich freely.
                Self-host internally without restrictions.
                If you offer Ehrlich as a network service, modifications must be open-sourced.
              </p>
            </div>
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                Commercial License
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Companies that want private modifications purchase an AGPL exemption.
                Includes commercial support, SLA, and custom domain development.
                Precedent: MongoDB, Confluent, GitLab, Spree Commerce.
              </p>
            </div>
            <div>
              <h3 className="text-foreground text-lg font-bold mb-2">
                67 Tools, Domain-Agnostic
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Chemistry, literature, analysis, prediction, simulation, training,
                nutrition, visualization, and statistics. Each tagged with domain
                metadata for automatic filtering. Add a{" "}
                <code className="font-mono text-xs text-primary">DomainConfig</code>{" "}
                and the engine handles the rest.
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

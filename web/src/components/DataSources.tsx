import { useRef, useEffect, useState } from "react";
import { motion, useInView, useSpring, useReducedMotion } from "motion/react";
import { DATA_SOURCES } from "@/lib/constants";
import { DATA_SOURCES_ASCII } from "@/lib/ascii-patterns";
import { SectionHeader } from "./SectionHeader";

const ACCESS_STYLES = {
  Internal: "text-accent border border-accent/30",
  "API Key": "text-muted-foreground border border-border",
  Free: "text-secondary border border-secondary/30",
} as const;

const DOMAIN_GROUPS = [
  {
    label: "MOLECULAR",
    sources: ["ChEMBL", "PubChem", "RCSB PDB", "UniProt", "Open Targets", "EPA CompTox", "GtoPdb"],
  },
  {
    label: "TRAINING",
    sources: ["ClinicalTrials.gov", "Semantic Scholar"],
  },
  {
    label: "NUTRITION",
    sources: ["NIH DSLD", "USDA FoodData", "OpenFDA CAERS"],
  },
  {
    label: "INTERNAL",
    sources: ["Ehrlich FTS5"],
  },
] as const;

function AnimatedCount({ target }: { target: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const spring = useSpring(0, { stiffness: 40, damping: 18 });
  const [display, setDisplay] = useState(reduced ? target : 0);

  useEffect(() => {
    if (isInView) spring.set(target);
  }, [isInView, target, spring]);

  useEffect(() => {
    return spring.on("change", (v) => setDisplay(Math.round(v)));
  }, [spring]);

  return <span ref={ref}>{display}</span>;
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};

const itemVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export function DataSources() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();

  return (
    <section id="data-sources" className="relative py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <div className="ascii-bg">
        <pre>{DATA_SOURCES_ASCII}</pre>
      </div>

      <SectionHeader title="Data Sources" />

      <div className="mb-10 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Real Data, Not Hallucinations
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          Every finding links back to its source. Every tool calls a real API.
          Every number is verifiable.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8">
        <div className="lg:col-span-3">
          <span className="font-mono text-8xl tracking-tighter text-primary leading-none">
            <AnimatedCount target={15} />
          </span>
          <span className="font-mono text-xs text-muted-foreground/60 uppercase tracking-wider block mt-2">
            databases queried
          </span>
        </div>

        <motion.div
          ref={ref}
          initial={reduced ? false : "hidden"}
          animate={isInView ? "visible" : "hidden"}
          variants={containerVariants}
          className="lg:col-span-9 space-y-8"
        >
          {DOMAIN_GROUPS.map((group) => (
            <div key={group.label}>
              <span className="font-mono text-[10px] text-muted-foreground/50 uppercase tracking-wider mb-3 block">
                {group.label}
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-1">
                {group.sources.map((sourceName) => {
                  const source = DATA_SOURCES.find((s) => s.name === sourceName);
                  if (!source) return null;
                  return (
                    <motion.div
                      key={source.name}
                      variants={itemVariants}
                      className="flex items-baseline justify-between py-2 border-b border-border/50 group"
                    >
                      <div className="flex items-baseline gap-2">
                        <span className="text-foreground font-medium group-hover:text-primary transition-colors">
                          {source.name}
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground/70 hidden sm:inline-block">
                          {source.domain}
                        </span>
                      </div>
                      <span
                        className={`font-mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-[1px] ${ACCESS_STYLES[source.access]}`}
                      >
                        {source.access}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

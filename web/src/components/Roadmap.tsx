import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { PLANNED_FEATURES } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export function Roadmap() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  const domains = PLANNED_FEATURES.filter((f) => f.type === "domain");
  const features = PLANNED_FEATURES.filter((f) => f.type === "feature");

  return (
    <section className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <SectionHeader title="Roadmap" />

      <div className="mb-12 max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Three domains today. Any domain tomorrow.
        </h2>
        <p className="text-base text-muted-foreground leading-relaxed">
          The engine is domain-agnostic. Register a{" "}
          <code className="font-mono text-xs text-primary">DomainConfig</code> with tools,
          data sources, and scoring definitions. The orchestrator, methodology, and visualization
          pipeline work identically across all domains.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
      >
        {/* Planned domains */}
        <div className="mb-8">
          <span className="font-mono text-[10px] text-muted-foreground/60 uppercase tracking-wider block mb-4">
            Planned Domains
          </span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {domains.map((item) => (
              <motion.div
                key={item.label}
                variants={itemVariants}
                className="border border-dashed border-border/50 rounded-sm p-5 hover:border-primary/40 transition-colors"
              >
                <h3 className="font-mono text-sm tracking-[0.08em] uppercase text-muted-foreground/60 mb-2">
                  {item.label}
                </h3>
                <p className="text-sm text-muted-foreground/60 leading-relaxed">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Platform features */}
        <div>
          <span className="font-mono text-[10px] text-muted-foreground/60 uppercase tracking-wider block mb-4">
            Platform Features
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {features.map((item) => (
              <motion.div
                key={item.label}
                variants={itemVariants}
                className="border border-dashed border-border/50 rounded-sm p-5 hover:border-primary/40 transition-colors"
              >
                <h3 className="font-mono text-sm tracking-[0.08em] uppercase text-foreground/70 mb-2">
                  {item.label}
                </h3>
                <p className="text-sm text-muted-foreground/60 leading-relaxed">
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
}

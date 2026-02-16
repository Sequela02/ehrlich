import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { SectionHeader } from "./SectionHeader";

const PERSONAS = [
  {
    label: "Student",
    usage: "Free Haiku. 3 investigations/month.",
    description: "Learn scientific methodology by doing it. Every investigation teaches hypothesis design, experimental controls, and evidence evaluation. Same tools the professionals use.",
  },
  {
    label: "Academic Researcher",
    usage: "Monthly credits. Sonnet for routine, Opus for publications.",
    description: "Run systematic reviews, test hypotheses across domains, build on prior findings through self-referential search. Full audit trail for reproducibility.",
  },
  {
    label: "Industry / Pharma",
    usage: "BYOK. Your Anthropic key, our methodology + tools.",
    description: "85 computational tools, 18 external APIs, structured reporting. Commercial license for private modifications. Self-host or use the hosted instance with your own Anthropic key.",
  },
] as const;

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function WhoItsFor() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <section id="who-its-for" className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <SectionHeader title="Who It's For" />

      <div className="mb-12 max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Same product at every level.
        </h2>
        <p className="text-base text-muted-foreground leading-relaxed">
          All 85 tools, all 19 data sources, and the full 6-phase methodology at every tier.
          The only variable is the Director model quality.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {PERSONAS.map((persona) => (
          <motion.div
            key={persona.label}
            variants={cardVariants}
            className="bg-surface border border-border rounded-sm p-6 lg:p-8 hover:border-primary/40 transition-colors group"
          >
            <h3 className="font-mono text-sm tracking-[0.12em] uppercase text-foreground group-hover:text-primary transition-colors mb-1">
              {persona.label}
            </h3>
            <span className="font-mono text-[11px] text-primary/70 block mb-4">
              {persona.usage}
            </span>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {persona.description}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}

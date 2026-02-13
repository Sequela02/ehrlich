import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { DIFFERENTIATORS } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function Differentiators() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <section
      id="differentiators"
      className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border"
    >
      <SectionHeader title="Why Ehrlich" />

      <div className="mb-12 max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          What makes this different
        </h2>
        <p className="text-base text-muted-foreground leading-relaxed">
          The AI implements the scientific methodology. It doesn&apos;t invent it.
          Tools execute on real data. Findings link to real sources.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {DIFFERENTIATORS.map((diff) => (
          <motion.div
            key={diff.label}
            variants={cardVariants}
            className="bg-surface border border-border rounded-sm p-6 lg:p-8 hover:border-primary/40 transition-colors group flex flex-col"
          >
            <div className="mb-6">
              <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors mb-1">
                {diff.label}
              </h3>
              <span className="font-mono text-[11px] text-muted-foreground/70">
                {diff.tagline}
              </span>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed mb-6">
              {diff.description}
            </p>

            <div className="mt-auto pt-4 border-t border-border/50">
              <ul className="space-y-1.5">
                {diff.capabilities.map((cap) => (
                  <li
                    key={cap}
                    className="font-mono text-[11px] text-muted-foreground/70 flex items-start gap-2"
                  >
                    <span className="text-primary mt-0.5 shrink-0">&bull;</span>
                    {cap}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}

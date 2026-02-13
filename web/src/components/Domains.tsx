import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { DOMAINS } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const COL_SPANS = [
  "md:col-span-12 lg:col-span-5",
  "md:col-span-6 lg:col-span-4",
  "md:col-span-6 lg:col-span-3",
] as const;

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
          Three Domains. One Engine.
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          Add your own with a{" "}
          <code className="font-mono text-xs text-primary">DomainConfig</code>{" "}
          &mdash; zero changes to existing code.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial={reduced ? false : "hidden"}
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="grid grid-cols-1 md:grid-cols-12 gap-4 lg:gap-6"
      >
        {DOMAINS.map((domain, i) => (
          <motion.div
            key={domain.label}
            variants={cardVariants}
            whileHover={{ y: -2, transition: { type: "spring", stiffness: 400, damping: 25 } }}
            className={`${COL_SPANS[i]} bg-surface border border-border rounded-sm p-6 lg:p-8 hover:border-primary transition-all duration-300 group flex flex-col h-full`}
          >
            <div className="flex justify-between items-start mb-6">
              <h4 className="font-mono text-sm tracking-[0.12em] uppercase text-foreground group-hover:text-primary transition-colors">
                {domain.label}
              </h4>
              <span className="font-mono text-[10px] text-primary border border-primary/20 bg-primary/5 px-2 py-1 rounded-[1px]">
                {domain.toolCount} TOOLS
              </span>
            </div>

            <div className="flex-grow">
              <span className="font-mono text-[10px] text-muted-foreground/70 mb-2 uppercase block">
                Capabilities
              </span>
              <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                {domain.capabilities}
              </p>

              <span className="font-mono text-[10px] text-muted-foreground/70 mb-2 uppercase block">
                Sources
              </span>
              <p className="font-mono text-[10px] text-muted-foreground/70 leading-relaxed">
                {domain.sources}
              </p>
            </div>

            <div className="mt-auto pt-6">
              <div className="bg-background border border-border p-3 rounded-sm">
                <span className="font-mono text-[9px] text-muted-foreground/50 mb-1 select-none block">
                  PROMPT:
                </span>
                <code className="font-mono text-[11px] text-muted-foreground block">
                  {domain.prompt}
                </code>
              </div>
            </div>
          </motion.div>
        ))}

        {/* Ghost "Your Domain" card */}
        <motion.div
          variants={cardVariants}
          className="md:col-span-12 bg-transparent border border-dashed border-border/50 rounded-sm p-6 lg:p-8 hover:border-primary/50 transition-colors flex flex-col items-center justify-center text-center min-h-[140px]"
        >
          <span className="font-mono text-sm tracking-[0.12em] uppercase text-muted-foreground/60 mb-2">
            Your Domain
          </span>
          <p className="text-sm text-muted-foreground/50 max-w-md">
            Implement{" "}
            <code className="font-mono text-xs text-primary/60">DomainConfig</code>{" "}
            + register tools. The engine handles the rest.
          </p>
        </motion.div>
      </motion.div>
    </section>
  );
}

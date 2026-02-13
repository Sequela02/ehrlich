import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { SectionHeader } from "./SectionHeader";
import { ARCHITECTURE_ASCII } from "@/lib/ascii-patterns";

const CARD_STYLES = {
  accent: {
    bar: "bg-accent",
    hover: "hover:border-accent",
    text: "text-accent",
  },
  primary: {
    bar: "bg-primary",
    hover: "hover:border-primary",
    text: "text-primary",
  },
  secondary: {
    bar: "bg-secondary",
    hover: "hover:border-secondary",
    text: "text-secondary",
  },
} as const;

function ModelCard({
  label,
  model,
  variant,
  children,
}: {
  label: string;
  model: string;
  variant: keyof typeof CARD_STYLES;
  children: React.ReactNode;
}) {
  const styles = CARD_STYLES[variant];

  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ y: -2, transition: { type: "spring", stiffness: 400, damping: 25 } }}
      className={`w-full max-w-md bg-background border border-border rounded-sm p-5 ${styles.hover} transition-colors group relative`}
    >
      <div className={`absolute top-0 left-0 w-1 h-full ${styles.bar} opacity-50 group-hover:opacity-100 transition-opacity`} />
      <div className="flex justify-between items-start mb-2">
        <span className={`font-mono text-[10px] ${styles.text} tracking-[0.12em] uppercase`}>
          {label}
        </span>
        <span className="font-mono text-xs text-foreground/70 bg-surface px-2 py-0.5 rounded-sm border border-border">
          {model}
        </span>
      </div>
      {children}
    </motion.div>
  );
}

function Connector() {
  return (
    <motion.div
      variants={connectorVariants}
      className="flex justify-center"
      style={{ transformOrigin: "top" }}
    >
      <div className="h-12 w-px bg-border" />
    </motion.div>
  );
}

function Fork() {
  return (
    <motion.div variants={connectorVariants} className="flex justify-center" style={{ transformOrigin: "top" }}>
      <div className="relative w-full max-w-md">
        <div className="flex justify-center">
          <div className="h-6 w-px bg-border" />
        </div>
        <div className="h-px bg-border mx-[25%]" />
        <div className="flex justify-between mx-[25%]">
          <div className="h-6 w-px bg-border" />
          <div className="h-6 w-px bg-border" />
        </div>
      </div>
    </motion.div>
  );
}

function Merge() {
  return (
    <motion.div variants={connectorVariants} className="flex justify-center" style={{ transformOrigin: "bottom" }}>
      <div className="relative w-full max-w-md">
        <div className="flex justify-between mx-[25%]">
          <div className="h-6 w-px bg-border" />
          <div className="h-6 w-px bg-border" />
        </div>
        <div className="h-px bg-border mx-[25%]" />
        <div className="flex justify-center">
          <div className="h-6 w-px bg-border" />
        </div>
      </div>
    </motion.div>
  );
}

const orchestrationVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.15, delayChildren: 0.1 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 200, damping: 20 },
  },
};

const connectorVariants = {
  hidden: { opacity: 0, scaleY: 0 },
  visible: {
    opacity: 1,
    scaleY: 1,
    transition: { duration: 0.3, ease: "easeOut" as const },
  },
};

export function Architecture() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });
  const reduced = useReducedMotion();

  return (
    <section id="architecture" className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto relative border-t border-border">
      <div className="ascii-bg">
        <pre>{ARCHITECTURE_ASCII}</pre>
      </div>

      <SectionHeader title="Architecture" />

      <div className="mb-10 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Three AI Models Working Together
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          One model reasons and plans. Two execute experiments in parallel. A
          fourth compresses and grades. Each optimized for its role &mdash;
          keeping costs low and quality high.
        </p>
      </div>

      <div className="w-full bg-surface border border-border rounded-sm p-8 lg:p-12 relative overflow-hidden">
        {/* Subtle grid background */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(to right, var(--color-border) 1px, transparent 1px), linear-gradient(to bottom, var(--color-border) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        <motion.div
          ref={ref}
          initial={reduced ? false : "hidden"}
          animate={isInView ? "visible" : "hidden"}
          variants={orchestrationVariants}
          className="relative z-10 flex flex-col items-center"
        >
          {/* Director */}
          <ModelCard label="DIRECTOR" model="Opus 4.6" variant="accent">
            <p className="text-sm text-muted-foreground">
              Formulates hypotheses, designs experiments, evaluates evidence,
              synthesizes conclusions. Extended thinking.{" "}
              <span className="text-destructive/80">No tool access.</span>
            </p>
          </ModelCard>

          <Fork />

          {/* Researchers */}
          <motion.div
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: 0.08 } },
            }}
            className="flex flex-col md:flex-row gap-6 w-full max-w-[calc(32rem+1.5rem)] justify-center"
          >
            <ModelCard label="RESEARCHER 01" model="Sonnet 4.5" variant="primary">
              <div className="mb-2">
                <span className="inline-block font-mono text-[9px] border border-primary/30 text-primary px-1.5 py-0.5 rounded-[1px]">
                  65 TOOLS
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Executes experiments with domain-filtered tools. Real API calls
                to ChEMBL, PubChem, RCSB PDB, and 12 more.
              </p>
            </ModelCard>

            <ModelCard label="RESEARCHER 02" model="Sonnet 4.5" variant="primary">
              <div className="mb-2">
                <span className="inline-block font-mono text-[9px] border border-primary/30 text-primary px-1.5 py-0.5 rounded-[1px]">
                  65 TOOLS
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Parallel execution. Literature synthesis &amp; negative control
                validation.
              </p>
            </ModelCard>
          </motion.div>

          <Merge />

          {/* Summarizer */}
          <ModelCard label="SUMMARIZER" model="Haiku 4.5" variant="secondary">
            <p className="text-sm text-muted-foreground">
              Compresses outputs &gt;2000 chars. PICO decomposition, evidence
              grading, and confidence scoring.
            </p>
          </ModelCard>
        </motion.div>
      </div>
    </section>
  );
}

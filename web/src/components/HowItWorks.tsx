import { useRef } from "react";
import {
  FlaskConical,
  BookOpen,
  Lightbulb,
  TestTube2,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { METHODOLOGY_ASCII } from "@/lib/ascii-patterns";
import { SectionHeader } from "./SectionHeader";

const PHASES = [
  {
    number: "01",
    label: "Classification & PICO",
    icon: FlaskConical,
    description:
      "Decompose your question into Population, Intervention, Comparison, Outcome. Auto-detect which scientific domains apply.",
  },
  {
    number: "02",
    label: "Literature Survey",
    icon: BookOpen,
    description:
      "Systematic search with citation chasing. GRADE-adapted body-of-evidence grading. AMSTAR-2 quality self-assessment.",
  },
  {
    number: "03",
    label: "Hypothesis Formulation",
    icon: Lightbulb,
    description:
      "Generate falsifiable hypotheses with predictions, null predictions, success criteria, failure criteria, scope, and prior confidence.",
  },
  {
    number: "04",
    label: "Experiment Testing",
    icon: TestTube2,
    description:
      "Parallel execution: 2 experiments per batch. 65 tools across chemistry, literature, analysis, prediction, simulation, training, and nutrition.",
  },
  {
    number: "05",
    label: "Negative Controls",
    icon: ShieldCheck,
    description:
      "Validate predictions with known-inactive compounds. Z\u2032-factor assay quality scoring. Permutation significance testing.",
  },
  {
    number: "06",
    label: "Synthesis",
    icon: FileText,
    description:
      "GRADE certainty grading. Priority tiers. Structured limitations taxonomy. Knowledge gap analysis. Follow-up recommendations.",
  },
] as const;

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });
  const reduced = useReducedMotion();

  return (
    <section
      id="how-it-works"
      className="relative py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border"
    >
      <div className="ascii-bg">
        <pre>{METHODOLOGY_ASCII}</pre>
      </div>

      <SectionHeader title="How It Works" />

      <div className="mb-12 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Six Phases of Rigorous Discovery
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          Every investigation follows a structured scientific protocol. Ehrlich
          doesn&apos;t just search the internet &mdash; it formulates hypotheses,
          designs experiments, tests them against real data, and grades the
          evidence.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial={reduced ? false : "hidden"}
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="relative"
      >
        {/* Vertical connecting line */}
        <motion.div
          className="absolute left-[19px] top-0 bottom-0 w-px bg-border hidden lg:block"
          initial={reduced ? false : { scaleY: 0 }}
          animate={isInView ? { scaleY: 1 } : {}}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          style={{ transformOrigin: "top" }}
        />

        <div className="space-y-6 lg:space-y-4">
          {PHASES.map((phase) => {
            const Icon = phase.icon;
            return (
              <motion.div
                key={phase.number}
                variants={itemVariants}
                className="flex gap-5 lg:gap-6 group"
              >
                {/* Phase number + icon */}
                <div className="flex-shrink-0 flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-sm border border-border bg-surface flex items-center justify-center group-hover:border-primary transition-colors relative z-10">
                    <Icon
                      size={18}
                      className="text-muted-foreground group-hover:text-primary transition-colors"
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 pb-4 border-b border-border/50 lg:border-b-0 lg:pb-0">
                  <div className="flex items-baseline gap-3 mb-1">
                    <span className="font-mono text-xs text-primary tracking-wider">
                      {phase.number}
                    </span>
                    <h4 className="font-mono text-sm uppercase tracking-[0.08em] text-foreground group-hover:text-primary transition-colors">
                      {phase.label}
                    </h4>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed max-w-lg">
                    {phase.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </section>
  );
}

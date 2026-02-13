import { useRef } from "react";
import {
  FlaskConical,
  BookOpen,
  Lightbulb,
  TestTube2,
  ShieldCheck,
  FileText,
} from "lucide-react";
import { motion, useInView } from "motion/react";
import { METHODOLOGY_PHASES } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const PHASE_ICONS = [FlaskConical, BookOpen, Lightbulb, TestTube2, ShieldCheck, FileText];

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

  return (
    <section
      id="how-it-works"
      className="relative py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border"
    >
      <SectionHeader title="How It Works" />

      <div className="mb-12 max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Six phases. Each grounded in established science.
        </h2>
        <p className="text-base text-muted-foreground leading-relaxed">
          Every investigation follows a structured scientific protocol. Ehrlich
          doesn&apos;t just search the internet &mdash; it formulates hypotheses,
          designs experiments, tests them against real data, validates with controls,
          and grades the evidence using peer-reviewed frameworks.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="relative"
      >
        {/* Vertical connecting line */}
        <motion.div
          className="absolute left-[19px] top-0 bottom-0 w-px bg-border hidden lg:block"
          initial={{ scaleY: 0 }}
          animate={isInView ? { scaleY: 1 } : {}}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          style={{ transformOrigin: "top" }}
        />

        <div className="space-y-6 lg:space-y-4">
          {METHODOLOGY_PHASES.map((phase, i) => {
            const Icon = PHASE_ICONS[i];
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
                  <div className="flex items-baseline gap-3 mb-1 flex-wrap">
                    <span className="font-mono text-xs text-primary tracking-wider">
                      {phase.number}
                    </span>
                    <h3 className="font-mono text-sm uppercase tracking-[0.08em] text-foreground group-hover:text-primary transition-colors">
                      {phase.label}
                    </h3>
                    <span className="font-mono text-[10px] text-accent/70 border border-accent/20 bg-accent/5 px-1.5 py-0.5 rounded">
                      {phase.foundation}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed max-w-xl">
                    {phase.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Hypothesis structure callout */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="mt-16 grid md:grid-cols-2 gap-6"
      >
        <div className="border border-border bg-surface/30 rounded-sm p-6">
          <h3 className="font-mono text-[10px] text-primary uppercase tracking-wider mb-4">
            Every Hypothesis Carries
          </h3>
          <div className="space-y-2 font-mono text-[11px] text-muted-foreground">
            <div><span className="text-foreground/70 inline-block w-28">statement</span> The core claim</div>
            <div><span className="text-foreground/70 inline-block w-28">prediction</span> What should be true if correct</div>
            <div><span className="text-foreground/70 inline-block w-28">null_prediction</span> What to expect if wrong</div>
            <div><span className="text-foreground/70 inline-block w-28">success_criteria</span> Measurable threshold for support</div>
            <div><span className="text-foreground/70 inline-block w-28">failure_criteria</span> Measurable threshold for refutation</div>
            <div><span className="text-foreground/70 inline-block w-28">prior_confidence</span> Bayesian prior (0-1)</div>
          </div>
        </div>

        <div className="border border-border bg-surface/30 rounded-sm p-6">
          <h3 className="font-mono text-[10px] text-primary uppercase tracking-wider mb-4">
            Every Experiment Carries
          </h3>
          <div className="space-y-2 font-mono text-[11px] text-muted-foreground">
            <div><span className="text-foreground/70 inline-block w-28">independent_var</span> What is being manipulated</div>
            <div><span className="text-foreground/70 inline-block w-28">dependent_var</span> What is being measured</div>
            <div><span className="text-foreground/70 inline-block w-28">controls</span> Positive and negative controls</div>
            <div><span className="text-foreground/70 inline-block w-28">confounders</span> Known confounding variables</div>
            <div><span className="text-foreground/70 inline-block w-28">analysis_plan</span> Statistical approach + thresholds</div>
            <div><span className="text-foreground/70 inline-block w-28">sensitivity</span> How robust to parameter changes</div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

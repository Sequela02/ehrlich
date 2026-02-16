import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Cpu, Activity, FileText, Network } from "lucide-react";

const CARD_STYLES = {
  accent: {
    border: "border-accent/50",
    bg: "bg-accent/5",
    text: "text-accent",
    icon: Cpu,
  },
  primary: {
    border: "border-primary/50",
    bg: "bg-primary/5",
    text: "text-primary",
    icon: Activity,
  },
  secondary: {
    border: "border-secondary/50",
    bg: "bg-secondary/5",
    text: "text-secondary",
    icon: FileText,
  },
} as const;

type TierKey = "haiku" | "sonnet" | "opus";

interface TierConfig {
  label: string;
  credits: number;
  tag: string;
  director: string;
  researcher: string;
  summarizer: string;
  directorReason: string;
  researcherReason: string;
  summarizerReason: string;
}

const TIERS: Record<TierKey, TierConfig> = {
  haiku: {
    label: "Haiku",
    credits: 1,
    tag: "Fast & efficient",
    director: "Haiku 4.5",
    researcher: "Haiku 4.5",
    summarizer: "Haiku 4.5",
    directorReason: "WHY: Fastest iteration. Lightweight reasoning for exploratory queries.",
    researcherReason: "WHY: Fast tool execution. Domain-filtered to only relevant tools.",
    summarizerReason: "WHY: Native compression speed. Consistent across the entire pipeline.",
  },
  sonnet: {
    label: "Sonnet",
    credits: 3,
    tag: "Balanced",
    director: "Sonnet 4.5",
    researcher: "Sonnet 4.5",
    summarizer: "Haiku 4.5",
    directorReason: "WHY: Strong reasoning at moderate cost. Good hypothesis quality.",
    researcherReason: "WHY: Fast tool execution. Domain-filtered to only relevant tools.",
    summarizerReason: "WHY: Compression is mechanical, not creative. Haiku handles it efficiently.",
  },
  opus: {
    label: "Opus",
    credits: 5,
    tag: "Maximum power",
    director: "Opus 4.6",
    researcher: "Sonnet 4.5",
    summarizer: "Haiku 4.5",
    directorReason: "WHY: Hypothesis quality requires deep reasoning. No tool access -- pure scientific thinking.",
    researcherReason: "WHY: Fast tool execution. Domain-filtered to only relevant tools.",
    summarizerReason: "WHY: Compression is mechanical, not creative. Haiku is 60x cheaper than Opus.",
  },
};

function ModelCard({
  label,
  model,
  variant,
  reason,
  children,
  delay = 0,
}: {
  label: string;
  model: string;
  variant: keyof typeof CARD_STYLES;
  reason: string;
  children: React.ReactNode;
  delay?: number;
}) {
  const styles = CARD_STYLES[variant];
  const Icon = styles.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ y: -4, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)" }}
      className={`relative w-full max-w-sm border ${styles.border} ${styles.bg} backdrop-blur-sm rounded-lg p-6 group overflow-hidden`}
    >
      <div className={`absolute top-0 left-0 w-full h-1 ${styles.bg.replace("/5", "/40")} origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-500`} />

      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-md ${styles.bg} ${styles.text}`}>
            <Icon size={18} />
          </div>
          <div>
            <div className={`font-mono text-[10px] ${styles.text} bg-black/40 px-2 py-0.5 rounded border ${styles.border} uppercase tracking-wider mb-1 inline-block`}>
              {label}
            </div>
            <AnimatePresence mode="wait">
              <motion.div
                key={model}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                className="font-bold text-lg leading-none"
              >
                {model}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="text-sm text-muted-foreground/80 leading-relaxed mb-3">
        {children}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={reason}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className={`font-mono text-[10px] ${styles.text} opacity-70`}
        >
          {reason}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}

function DataPipe({ height = 40, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      whileInView={{ opacity: 1, height }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
      className="w-px border-l border-dashed border-border relative flex justify-center"
    >
      <motion.div
        animate={{ top: ["0%", "100%"], opacity: [0, 1, 0] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "linear", delay }}
        className="absolute w-1.5 h-3 bg-foreground/50 rounded-full"
      />
    </motion.div>
  );
}

function TierSelector({ tier, onSelect }: { tier: TierKey; onSelect: (t: TierKey) => void }) {
  const keys: TierKey[] = ["haiku", "sonnet", "opus"];

  return (
    <div className="inline-flex items-center rounded-lg border border-border bg-surface/50 backdrop-blur-sm p-1 gap-1">
      {keys.map((key) => {
        const t = TIERS[key];
        const isActive = tier === key;
        return (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className={`relative px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              isActive
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground/80"
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="tier-bg"
                className="absolute inset-0 bg-primary/15 border border-primary/30 rounded-md"
                transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              {t.label}
              <span className="font-mono text-[10px] text-muted-foreground">
                {t.credits}cr
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function Architecture() {
  const [tier, setTier] = useState<TierKey>("opus");
  const config = TIERS[tier];

  return (
    <section
      id="architecture"
      className="relative py-32 px-4 lg:px-0 overflow-hidden bg-surface/30"
      style={{
        backgroundImage: "radial-gradient(oklch(0.22 0.01 155) 1px, transparent 1px)",
        backgroundSize: "32px 32px",
      }}
    >
      {/* Amber accent glow -- matches Director's accent color */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[300px] bg-accent/4 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 rounded-full border border-border bg-surface/50 backdrop-blur-sm">
            <Network size={14} className="text-primary" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Multi-Model Architecture</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
            Choose your team, <span className="text-primary">match the task.</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
            Every investigation assembles a team of three specialized models.
            Pick the tier that fits your question -- from fast exploration to maximum reasoning power.
          </p>

          <TierSelector tier={tier} onSelect={setTier} />
        </div>

        <div className="flex flex-col items-center">
          {/* Tier 1: Director */}
          <ModelCard
            label="Director"
            model={config.director}
            variant="accent"
            reason={config.directorReason}
          >
            Formulates hypotheses with predictions, criteria, and Bayesian priors.
            Designs experiments with controls and confounders.
            Evaluates evidence and synthesizes findings with GRADE certainty.
            {tier === "opus" && (
              <span className="text-accent/80"> Streaming with 10K token extended thinking.</span>
            )}
          </ModelCard>

          <DataPipe height={60} delay={0.2} />

          {/* Tier 2: Researchers (Parallel) */}
          <div className="relative p-8 border border-border/40 rounded-2xl bg-black/20 backdrop-blur-sm grid md:grid-cols-2 gap-8 w-full max-w-4xl">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-background px-4 font-mono text-[10px] text-muted-foreground uppercase tracking-widest border border-border/40 rounded-full">
              Parallel Execution &middot; 2 experiments per batch
            </div>

            <div className="flex flex-col items-center">
              <ModelCard
                label="Researcher A"
                model={config.researcher}
                variant="primary"
                delay={0.4}
                reason={config.researcherReason}
              >
                Executes experiment protocol. Queries databases, trains models,
                runs statistical tests, screens candidates. Max 10 tool calls per experiment.
              </ModelCard>
            </div>
            <div className="flex flex-col items-center">
              <ModelCard
                label="Researcher B"
                model={config.researcher}
                variant="primary"
                delay={0.5}
                reason="WHY: Parallel execution halves wall-clock time per batch."
              >
                Independent experiment on a different hypothesis. Cross-references
                literature, validates controls, computes metrics.
              </ModelCard>
            </div>
          </div>

          <DataPipe height={60} delay={0.6} />

          {/* Tier 3: Summarizer */}
          <ModelCard
            label="Summarizer"
            model={config.summarizer}
            variant="secondary"
            delay={0.8}
            reason={config.summarizerReason}
          >
            Compresses tool outputs over 2000 characters. PICO decomposition. Domain
            classification. GRADE evidence grading. Keeps the Director focused on
            reasoning, not parsing.
          </ModelCard>
        </div>
      </div>
    </section>
  );
}

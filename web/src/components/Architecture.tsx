import { motion } from "motion/react";
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
            <div className="font-bold text-lg leading-none">{model}</div>
          </div>
        </div>
      </div>

      <div className="text-sm text-muted-foreground/80 leading-relaxed mb-3">
        {children}
      </div>

      <div className={`font-mono text-[10px] ${styles.text} opacity-70`}>
        {reason}
      </div>
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

export function Architecture() {
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
            A research team, <span className="text-primary">assembled per question.</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Every investigation assembles a team of three specialized models.
            A Director that thinks deeply. Researchers that execute in parallel.
            A Summarizer that compresses noise. Cost: ~$3-4 instead of ~$11 all-Opus.
          </p>
        </div>

        <div className="flex flex-col items-center">
          {/* Tier 1: Director */}
          <ModelCard
            label="Director"
            model="Opus 4.6"
            variant="accent"
            reason="WHY: Hypothesis quality requires deep reasoning. No tool access -- pure scientific thinking."
          >
            Formulates hypotheses with predictions, criteria, and Bayesian priors.
            Designs experiments with controls and confounders.
            Evaluates evidence and synthesizes findings with GRADE certainty.
            <span className="text-accent/80"> Streaming with 10K token extended thinking.</span>
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
                model="Sonnet 4.5"
                variant="primary"
                delay={0.4}
                reason="WHY: Fast tool execution. Domain-filtered to only relevant tools."
              >
                Executes experiment protocol. Queries databases, trains models,
                runs statistical tests, screens candidates. Max 10 tool calls per experiment.
              </ModelCard>
            </div>
            <div className="flex flex-col items-center">
              <ModelCard
                label="Researcher B"
                model="Sonnet 4.5"
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
            model="Haiku 4.5"
            variant="secondary"
            delay={0.8}
            reason="WHY: Compression is mechanical, not creative. Haiku is 60x cheaper than Opus."
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

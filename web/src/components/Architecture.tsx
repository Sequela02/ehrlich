import { useReveal } from "@/lib/use-reveal";
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
    <div className={`w-full max-w-md bg-background border border-border rounded-sm p-5 ${styles.hover} transition-colors group relative`}>
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
    </div>
  );
}

function Connector({ height = "h-12" }: { height?: string }) {
  return (
    <div className="flex justify-center">
      <div className={`${height} w-px bg-border`} />
    </div>
  );
}

function Fork() {
  return (
    <div className="flex justify-center">
      <div className="relative w-full max-w-md">
        {/* Vertical stem down */}
        <div className="flex justify-center">
          <div className="h-6 w-px bg-border" />
        </div>
        {/* Horizontal bar */}
        <div className="h-px bg-border mx-[25%]" />
        {/* Two vertical drops */}
        <div className="flex justify-between mx-[25%]">
          <div className="h-6 w-px bg-border" />
          <div className="h-6 w-px bg-border" />
        </div>
      </div>
    </div>
  );
}

function Merge() {
  return (
    <div className="flex justify-center">
      <div className="relative w-full max-w-md">
        {/* Two vertical stems up */}
        <div className="flex justify-between mx-[25%]">
          <div className="h-6 w-px bg-border" />
          <div className="h-6 w-px bg-border" />
        </div>
        {/* Horizontal bar */}
        <div className="h-px bg-border mx-[25%]" />
        {/* Single vertical drop */}
        <div className="flex justify-center">
          <div className="h-6 w-px bg-border" />
        </div>
      </div>
    </div>
  );
}

export function Architecture() {
  const revealRef = useReveal();

  return (
    <section id="architecture" className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto relative">
      <div className="ascii-bg">
        <pre>{ARCHITECTURE_ASCII}</pre>
      </div>

      <SectionHeader title="Architecture" />

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

        <div ref={revealRef} className="stagger-children relative z-10 flex flex-col items-center">
          {/* Director */}
          <ModelCard label="DIRECTOR" model="Opus 4.6" variant="accent">
            <p className="text-sm text-muted-foreground">
              Formulates hypotheses, designs experiments, evaluates evidence,
              synthesizes conclusions.{" "}
              <span className="text-destructive/80">No tool access.</span>
            </p>
          </ModelCard>

          <Fork />

          {/* Researchers */}
          <div className="flex flex-col md:flex-row gap-6 w-full max-w-[calc(32rem+1.5rem)] justify-center">
            <ModelCard label="RESEARCHER 01" model="Sonnet 4.5" variant="primary">
              <div className="mb-2">
                <span className="inline-block font-mono text-[9px] border border-primary/30 text-primary px-1.5 py-0.5 rounded-[1px]">
                  48 TOOLS
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Executes experiments with domain-filtered tools. Molecular
                simulations &amp; data retrieval.
              </p>
            </ModelCard>

            <ModelCard label="RESEARCHER 02" model="Sonnet 4.5" variant="primary">
              <div className="mb-2">
                <span className="inline-block font-mono text-[9px] border border-primary/30 text-primary px-1.5 py-0.5 rounded-[1px]">
                  48 TOOLS
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Parallel execution. Literature synthesis &amp; negative control
                validation.
              </p>
            </ModelCard>
          </div>

          <Merge />

          {/* Summarizer */}
          <ModelCard label="SUMMARIZER" model="Haiku 4.5" variant="secondary">
            <p className="text-sm text-muted-foreground">
              Compresses outputs, PICO decomposition, evidence grading, and
              confidence scoring.
            </p>
          </ModelCard>
        </div>
      </div>
    </section>
  );
}

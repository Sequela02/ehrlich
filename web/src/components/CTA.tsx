import { useRef, useState } from "react";
import { ArrowRight, Copy, Check } from "lucide-react";
import { motion, useInView } from "motion/react";
import { PRICING_TIERS } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const QUICKSTART = `git clone https://github.com/sequelcore/ehrlich
cd ehrlich/server && uv sync
export ANTHROPIC_API_KEY=sk-...
uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`;

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

export function CTA() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(QUICKSTART).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <section id="pricing" className="relative py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      {/* Primary accent glow -- final push */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-primary/3 rounded-full blur-[140px] pointer-events-none" />

      <SectionHeader title="Pricing" />

      <div className="mb-12 max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Same product at every tier.
        </h2>
        <p className="text-base text-muted-foreground leading-relaxed">
          No feature gates. All 67 tools, all 16 data sources, full 6-phase methodology
          at every level. The only variable is the Director model quality: Haiku reasons
          adequately, Sonnet reasons well, Opus reasons deeply.
        </p>
      </div>

      {/* Pricing cards */}
      <motion.div
        ref={ref}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20"
      >
        {PRICING_TIERS.map((tier) => (
          <motion.div
            key={tier.name}
            variants={cardVariants}
            className={`flex flex-col p-6 lg:p-8 rounded-sm border transition-colors ${
              tier.highlight
                ? "border-primary/50 bg-primary/5"
                : "border-border bg-surface"
            }`}
          >
            <div className="mb-6">
              <h3 className="font-mono text-sm uppercase tracking-[0.12em] text-foreground mb-2">
                {tier.name}
              </h3>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-foreground">{tier.price}</span>
                {tier.period && (
                  <span className="text-sm text-muted-foreground">{tier.period}</span>
                )}
              </div>
              <div className="font-mono text-[11px] text-muted-foreground/60 mt-1">
                {tier.credits}
              </div>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed mb-6">
              {tier.description}
            </p>

            <ul className="space-y-2 mb-8 flex-grow">
              {tier.features.map((feature) => (
                <li
                  key={feature}
                  className="font-mono text-[11px] text-muted-foreground flex items-start gap-2"
                >
                  <span className="text-primary mt-0.5 shrink-0">&bull;</span>
                  {feature}
                </li>
              ))}
            </ul>

            <a
              href="/console"
              className={`text-center font-medium text-sm px-6 py-3 rounded-sm flex items-center justify-center gap-2 transition-colors ${
                tier.highlight
                  ? "bg-primary text-primary-foreground hover:opacity-90"
                  : "border border-border text-foreground hover:border-primary hover:text-primary"
              }`}
            >
              {tier.cta}
              <ArrowRight size={14} />
            </a>
          </motion.div>
        ))}
      </motion.div>

      {/* Developer quickstart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          Or self-host.
        </h2>
        <p className="text-muted-foreground text-base mb-6 max-w-lg">
          Clone the repo, add your API key, run the server. No account needed.
          Full AGPL-3.0 access to everything.
        </p>

        <div className="terminal-frame max-w-2xl relative">
          <div className="terminal-header">
            <span className="terminal-dot" />
            <span className="terminal-dot" />
            <span className="terminal-dot" />
            <span className="ml-3 font-mono text-[10px] text-muted-foreground/60 uppercase tracking-wider">
              terminal
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="ml-auto font-mono text-[10px] text-muted-foreground/60 hover:text-primary transition-colors flex items-center gap-1.5 uppercase tracking-wider"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <div className="p-5">
            <pre className="font-mono text-xs text-muted-foreground leading-relaxed whitespace-pre overflow-x-auto">
              {QUICKSTART.split("\n").map((line, i) => (
                <div key={i}>
                  <span className="text-primary select-none">$ </span>
                  {line}
                </div>
              ))}
            </pre>
          </div>
        </div>
      </motion.div>

      {/* Final CTA */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="mt-20 pt-16 border-t border-border/50 text-center"
      >
        <h3 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground mb-4">
          Run your first investigation.
        </h3>
        <p className="text-muted-foreground text-base mb-8 max-w-lg mx-auto">
          Free tier. No credit card. 3 Haiku investigations per month.
          Full methodology. All tools.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a
            href="/console"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground font-medium text-sm px-8 py-3 rounded-sm hover:opacity-90 transition-opacity"
          >
            Start Free
            <ArrowRight size={14} />
          </a>
          <a
            href="https://github.com/sequelcore/ehrlich"
            className="inline-flex items-center gap-2 border border-border text-foreground font-medium text-sm px-8 py-3 rounded-sm hover:border-primary hover:text-primary transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </motion.div>
    </section>
  );
}

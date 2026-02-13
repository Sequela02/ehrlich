import { useRef, useState } from "react";
import { ArrowRight, Copy, Check } from "lucide-react";
import { motion, useInView, useReducedMotion } from "motion/react";

const QUICKSTART = `git clone https://github.com/sequelcore/ehrlich
cd ehrlich/server && uv sync
export ANTHROPIC_API_KEY=sk-...
uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`;

export function CTA() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(QUICKSTART).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <section className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <motion.div
        ref={ref}
        initial={reduced ? false : { opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6, ease: "easeOut" as const }}
      >
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
          Start Discovering
        </h2>

        <p className="text-muted-foreground text-base mb-10 max-w-lg">
          Ask your first scientific question. No account needed &mdash; Ehrlich
          runs locally with your own API key.
        </p>

        {/* Primary CTA */}
        <div className="flex flex-col md:flex-row gap-4 mb-16">
          <a
            href="/console"
            className="bg-primary text-primary-foreground hover:opacity-90 transition-colors font-medium text-sm px-8 py-4 rounded-sm flex items-center justify-center gap-2 group"
          >
            Try Ehrlich
            <ArrowRight
              size={16}
              className="transition-transform group-hover:translate-x-1"
            />
          </a>
          <a
            href="https://github.com/sequelcore/ehrlich"
            className="border border-border text-foreground hover:border-primary hover:text-primary transition-colors font-medium text-sm px-8 py-4 rounded-sm text-center"
          >
            View on GitHub
          </a>
        </div>

        {/* Developer quickstart -- secondary, for devs only */}
        <details className="group">
          <summary className="font-mono text-xs text-muted-foreground/60 uppercase tracking-wider cursor-pointer hover:text-primary transition-colors mb-4 select-none">
            Developer Quickstart
          </summary>
          <div className="terminal-frame max-w-2xl relative">
            <div className="terminal-header">
              <span className="terminal-dot" />
              <span className="terminal-dot" />
              <span className="terminal-dot" />
              <span className="ml-3 font-mono text-[10px] text-muted-foreground/50 uppercase tracking-wider">
                terminal
              </span>
              <button
                type="button"
                onClick={handleCopy}
                className="ml-auto font-mono text-[10px] text-muted-foreground/50 hover:text-primary transition-colors flex items-center gap-1.5 uppercase tracking-wider"
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
        </details>
      </motion.div>
    </section>
  );
}

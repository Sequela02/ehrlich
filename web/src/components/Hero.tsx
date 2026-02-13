import { useRef, useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import {
  motion,
  useInView,
  useScroll,
  useTransform,
  useSpring,
  useReducedMotion,
} from "motion/react";
import { STATS } from "@/lib/constants";
import { HERO_ASCII } from "@/lib/ascii-patterns";

const EXAMPLE_PROMPTS = [
  "Compare HIIT vs steady-state training for VO2max improvement",
  "Find antimicrobial compounds effective against MRSA",
  "Evaluate creatine supplementation for strength performance",
] as const;

function AnimatedCounter({ target }: { target: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const spring = useSpring(0, { stiffness: 50, damping: 20 });
  const [display, setDisplay] = useState(reduced ? target : 0);

  useEffect(() => {
    if (isInView) spring.set(target);
  }, [isInView, target, spring]);

  useEffect(() => {
    return spring.on("change", (v) => setDisplay(Math.round(v)));
  }, [spring]);

  return <span ref={ref}>{display}</span>;
}

function RotatingPlaceholder() {
  const [index, setIndex] = useState(0);
  const reduced = useReducedMotion();

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % EXAMPLE_PROMPTS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.span
      key={index}
      initial={reduced ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 0.5, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3 }}
      className="pointer-events-none select-none truncate"
    >
      {EXAMPLE_PROMPTS[index]}
    </motion.span>
  );
}

export function Hero() {
  const sectionRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(contentRef, { once: true });
  const reduced = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end start"],
  });
  const asciiY = useTransform(scrollYProgress, [0, 1], [0, -80]);

  return (
    <section
      ref={sectionRef}
      className="min-h-screen relative flex flex-col justify-center px-4 lg:px-0 max-w-[1200px] mx-auto border-l border-r border-border/30"
    >
      {/* ASCII background with parallax */}
      <motion.div className="ascii-bg" style={reduced ? undefined : { y: asciiY }}>
        <pre>{HERO_ASCII}</pre>
      </motion.div>

      <div ref={contentRef} className="relative z-10 w-full max-w-3xl">
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 24 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-primary/80 mb-4 block">
            Open Source &middot; AGPL-3.0
          </span>

          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter text-foreground mb-6">
            Ask any scientific question.
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed mb-10">
            Ehrlich is a hypothesis-driven research engine that designs
            experiments, queries real databases, and delivers evidence-graded
            answers &mdash; across molecular science, training science, and
            nutrition.
          </p>

          {/* Search prompt -- the primary CTA */}
          <div className="mb-6">
            <a
              href="/console"
              className="group flex items-center gap-3 w-full bg-surface border border-border hover:border-primary rounded-sm px-5 py-4 transition-colors"
            >
              <span className="flex-1 font-mono text-sm text-muted-foreground overflow-hidden">
                <RotatingPlaceholder />
              </span>
              <span className="flex-shrink-0 bg-primary text-primary-foreground px-4 py-2 rounded-sm font-mono text-xs uppercase tracking-wider flex items-center gap-2">
                Start Investigating
                <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
              </span>
            </a>
          </div>

          {/* Example prompts */}
          <div className="flex flex-wrap gap-2 mb-14">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <a
                key={prompt}
                href="/console"
                className="font-mono text-[10px] text-muted-foreground/60 hover:text-primary border border-border/50 hover:border-primary/30 px-3 py-1.5 rounded-sm transition-colors truncate max-w-[300px]"
              >
                {prompt}
              </a>
            ))}
          </div>

          {/* Stats bar with animated counters */}
          <div className="border-t border-border pt-6 flex flex-wrap gap-8 font-mono text-[11px] text-muted-foreground uppercase tracking-[0.12em]">
            <span>
              <span className="text-primary">
                <AnimatedCounter target={STATS.tools} />
              </span>{" "}
              tools
            </span>
            <span>
              <span className="text-primary">
                <AnimatedCounter target={STATS.dataSources} />
              </span>{" "}
              data sources
            </span>
            <span>
              <span className="text-primary">
                <AnimatedCounter target={STATS.domains} />
              </span>{" "}
              domains
            </span>
            <span>
              <span className="text-primary">
                <AnimatedCounter target={STATS.models} />
              </span>{" "}
              AI models
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { VISUALIZATION_CATEGORIES } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export function Visualizations() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();

  return (
    <section className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <SectionHeader title="Visualizations" />

      <div className="mb-12 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          The system picks the right visualization.
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          The orchestrator intercepts tool results and renders the matching visualization
          automatically. 3D molecular viewers for docking results. Statistical plots for
          meta-analysis. Anatomy diagrams for training. Node graphs for hypothesis tracking.
          No configuration needed.
        </p>
      </div>

      <motion.div
        ref={ref}
        initial={reduced ? false : "hidden"}
        animate={isInView ? "visible" : "hidden"}
        variants={containerVariants}
        className="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        {VISUALIZATION_CATEGORIES.map((category) => (
          <motion.div
            key={category.label}
            variants={cardVariants}
            className="bg-surface/30 border border-border rounded-sm p-6 hover:border-primary/40 transition-colors group"
          >
            <div className="flex items-baseline justify-between mb-4">
              <h4 className="font-mono text-sm tracking-[0.08em] uppercase text-foreground group-hover:text-primary transition-colors">
                {category.label}
              </h4>
              <span className="font-mono text-[10px] text-muted-foreground/40">
                {category.tech}
              </span>
            </div>

            <ul className="space-y-2">
              {category.items.map((item) => {
                const [name, ...descParts] = item.split(" -- ");
                const desc = descParts.join(" -- ");
                return (
                  <li
                    key={item}
                    className="font-mono text-[11px] text-muted-foreground leading-relaxed flex items-start gap-2"
                  >
                    <span className="text-primary mt-0.5 shrink-0">&bull;</span>
                    <span>
                      <span className="text-foreground/70">{name}</span>
                      {desc && <span className="text-muted-foreground/60"> &mdash; {desc}</span>}
                    </span>
                  </li>
                );
              })}
            </ul>
          </motion.div>
        ))}
      </motion.div>

      {/* Extensibility callout */}
      <motion.div
        initial={reduced ? false : { opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        className="mt-6 bg-transparent border border-dashed border-border/50 rounded-sm p-6 hover:border-primary/50 transition-colors"
      >
        <h4 className="font-mono text-sm tracking-[0.08em] uppercase text-muted-foreground/60 mb-2">
          Add Your Own
        </h4>
        <p className="text-sm text-muted-foreground/60 max-w-2xl leading-relaxed">
          When you register a new domain, you can create custom visualization components
          using any rendering library: Recharts, Visx, D3, custom SVG, WebGL, maps, network
          graphs. Register them in the{" "}
          <code className="font-mono text-[10px] text-primary/60">VizRegistry</code>{" "}
          by <code className="font-mono text-[10px] text-primary/60">viz_type</code> string.
          The orchestrator auto-intercepts any tool result containing that type and renders
          it inline. Suspense boundaries, grid layout, and error fallbacks are handled for you.
        </p>
      </motion.div>
    </section>
  );
}

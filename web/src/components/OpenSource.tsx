import { Github } from "lucide-react";
import { useReveal } from "@/lib/use-reveal";

const FEATURES = [
  {
    title: "Add a Domain",
    description: (
      <>
        Zero changes to existing code. Plug in a{" "}
        <span className="font-mono text-xs text-primary">DomainConfig</span> and
        register tools.
      </>
    ),
  },
  {
    title: "48 Tools",
    description:
      "Chemistry, literature, analysis, prediction, simulation, training, nutrition, visualization.",
  },
  {
    title: "Domain-Agnostic",
    description:
      "The engine handles any scientific domain. Currently: molecular, training, nutrition.",
  },
] as const;

export function OpenSource() {
  const revealRef = useReveal();

  return (
    <section className="py-32 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <div ref={revealRef} className="reveal-section flex flex-col items-start">
        <h2 className="text-5xl md:text-7xl font-bold tracking-tight text-foreground mb-6">
          <span className="text-primary">Open</span> Source
        </h2>

        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mb-16 leading-relaxed font-light">
          AGPL-3.0 licensed. Fork it, extend it, add your own scientific domain.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 w-full mb-16">
          {FEATURES.map((feature) => (
            <div key={feature.title}>
              <h3 className="text-foreground text-lg font-bold mb-3">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        <a
          href="https://github.com/sequelcore/ehrlich"
          className="font-mono text-sm text-foreground/80 hover:text-primary border border-border bg-surface px-4 py-2 rounded-sm flex items-center gap-3 transition-colors group"
        >
          <Github size={16} />
          github.com/sequelcore/ehrlich
        </a>
      </div>
    </section>
  );
}

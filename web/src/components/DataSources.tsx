import { useReveal } from "@/lib/use-reveal";
import { DATA_SOURCES } from "@/lib/constants";
import { DATA_SOURCES_ASCII } from "@/lib/ascii-patterns";
import { SectionHeader } from "./SectionHeader";

const ACCESS_STYLES = {
  Internal: "text-accent border border-accent/30",
  "API Key": "text-muted-foreground border border-border",
  Free: "text-secondary border border-secondary/30",
} as const;

export function DataSources() {
  const revealRef = useReveal();

  return (
    <section id="data-sources" className="relative py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <div className="ascii-bg">
        <pre>{DATA_SOURCES_ASCII}</pre>
      </div>

      <div ref={revealRef} className="reveal-section">
        <SectionHeader title="13 Data Sources" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8">
          <div className="lg:col-span-4">
            <span className="font-mono text-8xl tracking-tighter text-primary leading-none">
              13
            </span>
          </div>

          <div className="lg:col-span-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
              {DATA_SOURCES.map((source) => (
                <div
                  key={source.name}
                  className="flex items-baseline justify-between py-2 border-b border-border/50 group"
                >
                  <div className="flex items-baseline gap-2">
                    <span className="text-foreground font-medium group-hover:text-primary transition-colors">
                      {source.name}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground/70 hidden sm:inline-block">
                      {source.domain}
                    </span>
                  </div>
                  <span
                    className={`font-mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-[1px] ${ACCESS_STYLES[source.access]}`}
                  >
                    {source.access}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

import { useReveal } from "@/lib/use-reveal";
import { DOMAINS } from "@/lib/constants";
import { SectionHeader } from "./SectionHeader";

const COL_SPANS = [
  "md:col-span-12 lg:col-span-5",
  "md:col-span-6 lg:col-span-4",
  "md:col-span-6 lg:col-span-3",
] as const;

export function Domains() {
  const revealRef = useReveal();

  return (
    <section id="domains" className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <div ref={revealRef} className="reveal-section">
        <SectionHeader title="Scientific Domains" />

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 lg:gap-6">
          {DOMAINS.map((domain, i) => (
            <div
              key={domain.label}
              className={`${COL_SPANS[i]} bg-surface border border-border rounded-sm p-6 lg:p-8 hover:border-primary hover:-translate-y-[1px] transition-all duration-300 group flex flex-col h-full`}
            >
              <div className="flex justify-between items-start mb-6">
                <h3 className="font-mono text-sm tracking-[0.12em] uppercase text-foreground group-hover:text-primary transition-colors">
                  {domain.label}
                </h3>
                <span className="font-mono text-[10px] text-primary border border-primary/20 bg-primary/5 px-2 py-1 rounded-[1px]">
                  {domain.toolCount} TOOLS
                </span>
              </div>

              <div className="flex-grow">
                <span className="font-mono text-[10px] text-muted-foreground/70 mb-2 uppercase block">
                  Capabilities
                </span>
                <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                  {domain.capabilities}
                </p>

                <span className="font-mono text-[10px] text-muted-foreground/70 mb-2 uppercase block">
                  Sources
                </span>
                <p className="font-mono text-[10px] text-muted-foreground/70 leading-relaxed">
                  {domain.sources}
                </p>
              </div>

              <div className="mt-auto pt-6">
                <div className="bg-background border border-border p-3 rounded-sm">
                  <span className="font-mono text-[9px] text-muted-foreground/50 mb-1 select-none block">
                    PROMPT:
                  </span>
                  <code className="font-mono text-[11px] text-muted-foreground block">
                    {domain.prompt}
                  </code>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

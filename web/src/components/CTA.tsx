import { ArrowRight } from "lucide-react";
import { useReveal } from "@/lib/use-reveal";

const LINKS = [
  { label: "Launch Console", href: "/console", primary: true },
  { label: "Self-Host with Docker", href: "/docs/docker", primary: false },
  { label: "Read the Docs", href: "/docs", primary: false },
] as const;

export function CTA() {
  const revealRef = useReveal();

  return (
    <section className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <div ref={revealRef} className="reveal-section">
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
          Run your first investigation
        </h2>

        <p className="text-muted-foreground font-mono text-sm md:text-base mb-12">
          No account needed. Clone the repo, set your API key, start discovering.
        </p>

        <div className="flex flex-col md:flex-row gap-8 md:gap-12 text-sm font-medium">
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className={`flex items-center gap-2 group transition-colors ${
                link.primary
                  ? "text-primary hover:text-primary/80"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {link.label}
              <ArrowRight
                size={16}
                className="transition-transform group-hover:translate-x-1"
              />
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

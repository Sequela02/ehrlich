import { FOOTER_LINKS } from "@/lib/constants";

const SECTIONS = [
  { title: "Product", links: FOOTER_LINKS.product },
  { title: "Developers", links: FOOTER_LINKS.developers },
  { title: "Legal", links: FOOTER_LINKS.legal },
] as const;

export function Footer() {
  return (
    <footer className="border-t border-border py-12 bg-background">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div>
            <span className="font-sans font-semibold text-lg tracking-tight text-foreground block mb-3">
              Ehrlich
            </span>
            <p className="font-mono text-[11px] text-muted-foreground/60 leading-relaxed">
              Scientific methodology,<br />automated.
            </p>
          </div>

          {/* Link columns */}
          {SECTIONS.map((section) => (
            <div key={section.title}>
              <span className="font-mono text-[10px] text-muted-foreground/60 uppercase tracking-wider block mb-3">
                {section.title}
              </span>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className="font-mono text-xs text-muted-foreground hover:text-primary transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-border/50 pt-6 flex flex-col md:flex-row md:justify-between items-center gap-2">
          <span className="font-mono text-[10px] text-muted-foreground/60">
            AGPL-3.0 &middot; 2026
          </span>
          <span className="font-mono text-[10px] text-muted-foreground/60">
            Built by Sequel &middot; Born at the Claude Code Hackathon 2026
          </span>
        </div>
      </div>
    </footer>
  );
}

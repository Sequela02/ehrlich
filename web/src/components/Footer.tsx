import { FOOTER_LINKS } from "@/lib/constants";

export function Footer() {
  return (
    <footer className="border-t border-border py-8 bg-background">
      <div className="max-w-[1200px] mx-auto px-6 flex flex-col items-center gap-4 md:flex-row md:justify-between">
        <span className="font-mono text-xs text-muted-foreground/70 uppercase">
          Ehrlich &middot; AGPL-3.0 &middot; 2026
        </span>
        <div className="flex gap-6">
          {FOOTER_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs text-muted-foreground hover:text-primary transition-colors"
            >
              {link.label}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}

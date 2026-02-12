import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useScrollProgress } from "@/lib/use-scroll-progress";
import { NAV_LINKS } from "@/lib/constants";

export function Nav() {
  const [open, setOpen] = useState(false);
  const progress = useScrollProgress();

  return (
    <nav className="fixed top-0 left-0 right-0 h-12 bg-background/90 backdrop-blur-sm z-50 border-b border-border">
      <div className="max-w-[1200px] mx-auto h-full px-6 flex items-center justify-between">
        <a href="#" className="font-sans font-semibold text-lg tracking-tight text-foreground">
          Ehrlich
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-primary transition-colors"
            >
              {link.label}
            </a>
          ))}
          <a
            href="/console"
            className="ml-2 px-4 py-1.5 bg-primary text-primary-foreground font-mono text-xs uppercase tracking-wider rounded"
          >
            Launch Console
          </a>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          className="md:hidden text-muted-foreground hover:text-primary transition-colors"
          onClick={() => setOpen(!open)}
          aria-label={open ? "Close menu" : "Open menu"}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-background/95 backdrop-blur-sm border-b border-border px-6 py-4 flex flex-col gap-4">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <a
            href="/console"
            className="mt-2 px-4 py-1.5 bg-primary text-primary-foreground font-mono text-xs uppercase tracking-wider rounded text-center"
          >
            Launch Console
          </a>
        </div>
      )}

      {/* Scroll progress bar */}
      <div
        className="scroll-progress absolute bottom-0 left-0 right-0 bg-primary h-0.5"
        style={{ transform: `scaleX(${progress})` }}
      />
    </nav>
  );
}

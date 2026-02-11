import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
              <span className="inline-block h-4 w-1 rounded-sm bg-primary" />
              EHRLICH
            </a>
            <span className="rounded border border-primary/30 px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wider text-primary">
              alpha
            </span>
          </div>
          <span className="hidden font-mono text-[11px] tracking-wide text-muted-foreground sm:block">
            Antimicrobial Discovery
          </span>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

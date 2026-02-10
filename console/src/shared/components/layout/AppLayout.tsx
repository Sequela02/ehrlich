import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-7xl items-center px-6">
          <a href="/" className="text-lg font-semibold tracking-tight">
            Ehrlich
          </a>
          <span className="ml-2 rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            alpha
          </span>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

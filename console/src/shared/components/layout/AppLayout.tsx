import { useState, type ReactNode } from "react";
import { BookOpen, Coins, Key, LogIn, LogOut } from "lucide-react";
import { useAuth } from "@/shared/hooks/use-auth";
import { useCredits } from "@/features/investigation/hooks/use-credits";
import { Toaster } from "@/shared/components/ui/Toaster";
import { MethodologyDrawer } from "./MethodologyDrawer";

interface AppLayoutProps {
  children: ReactNode;
  hideHeader?: boolean;
}

export function AppLayout({ children, hideHeader }: AppLayoutProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { user, isLoading, signIn, signOut } = useAuth();
  const { data: creditData } = useCredits();

  return (
    <div className="min-h-screen bg-background">
      {!hideHeader && (
        <header className="border-b border-border">
          <div className="mx-auto flex h-12 max-w-[1200px] items-center justify-between px-6">
            <div className="flex items-center gap-3">
              <a href="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
                <span className="inline-block h-4 w-1 rounded-sm bg-primary" />
                EHRLICH
              </a>
              <span className="rounded border border-primary/30 px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-wider text-primary">
                alpha
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden font-mono text-[11px] tracking-wide text-muted-foreground sm:block">
                Scientific Discovery Engine
              </span>
              <button
                onClick={() => setDrawerOpen(true)}
                className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                title="Methodology"
                aria-label="Open methodology"
              >
                <BookOpen className="h-4 w-4" />
              </button>

              {!isLoading && (
                <>
                  {user ? (
                    <div className="flex items-center gap-2">
                      {creditData && (
                        <span className="inline-flex items-center gap-1 rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                          {creditData.is_byok ? (
                            <>
                              <Key className="h-3 w-3 text-primary" />
                              BYOK
                            </>
                          ) : (
                            <>
                              <Coins className="h-3 w-3 text-primary" />
                              {creditData.credits} cr
                            </>
                          )}
                        </span>
                      )}
                      <span className="hidden font-mono text-[11px] text-muted-foreground sm:block">
                        {user.email}
                      </span>
                      <button
                        onClick={() => signOut()}
                        className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                        title="Sign out"
                        aria-label="Sign out"
                      >
                        <LogOut className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => signIn()}
                      className="inline-flex items-center gap-1.5 rounded-sm px-3 py-1.5 font-mono text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    >
                      <LogIn className="h-3.5 w-3.5" />
                      Sign in
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </header>
      )}
      <main>{children}</main>
      <Toaster />
      <MethodologyDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  );
}

import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LogIn } from "lucide-react";
import { PromptInput, InvestigationList, TemplateCards, BYOKSettings } from "@/features/investigation/components";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";
import { useStats } from "@/features/investigation/hooks/use-stats";
import { useAuth } from "@/shared/hooks/use-auth";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: investigations } = useInvestigations();
  const { data: stats } = useStats();
  const { user, isLoading, signIn } = useAuth();
  const [prompt, setPrompt] = useState("");

  return (
    <div className="mx-auto max-w-4xl space-y-10 p-8">
      <div className="space-y-3">
        <h1 className="text-5xl font-bold tracking-tight">Ehrlich</h1>
        <p className="text-lg text-muted-foreground">
          AI-powered scientific discovery engine
        </p>
        <p className="font-mono text-xs text-muted-foreground/70">
          {stats ? (
            <Link
              to="/methodology"
              className="transition-colors hover:text-foreground"
            >
              {stats.tool_count} tools {"\u00b7"} {stats.phase_count} phases {"\u00b7"} {stats.domain_count} domains {"\u00b7"} {stats.data_source_count} data sources
            </Link>
          ) : (
            "loading\u2026"
          )}
        </p>
      </div>

      {!isLoading && !user ? (
        <div className="rounded-lg border border-border bg-surface p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Sign in to start an investigation
          </p>
          <button
            onClick={() => signIn()}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 hover:shadow-[0_0_12px_oklch(0.72_0.19_155_/_0.3)]"
          >
            <LogIn className="h-4 w-4" />
            Sign in
          </button>
        </div>
      ) : (
        <>
          <PromptInput value={prompt} onChange={setPrompt} />
          <BYOKSettings />
        </>
      )}

      <div className="space-y-3">
        <h2 className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Research Templates
        </h2>
        <TemplateCards onSelect={setPrompt} />
      </div>
      {investigations && investigations.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Recent Investigations
          </h2>
          <InvestigationList investigations={investigations} />
        </div>
      )}
    </div>
  );
}

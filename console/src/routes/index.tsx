import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PromptInput, InvestigationList, TemplateCards } from "@/features/investigation/components";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";
import { useStats } from "@/features/investigation/hooks/use-stats";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: investigations } = useInvestigations();
  const { data: stats } = useStats();
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
      <PromptInput value={prompt} onChange={setPrompt} />
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

import { createFileRoute } from "@tanstack/react-router";
import { PromptInput, InvestigationList } from "@/features/investigation/components";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: investigations } = useInvestigations();

  return (
    <div className="mx-auto max-w-4xl space-y-10 p-8">
      <div className="space-y-3">
        <h1 className="text-5xl font-bold tracking-tight">Ehrlich</h1>
        <p className="text-lg text-muted-foreground">
          AI-powered antimicrobial discovery agent
        </p>
        <p className="font-mono text-xs text-muted-foreground/70">
          19 tools · 7 phases · multi-model architecture
        </p>
      </div>
      <PromptInput />
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

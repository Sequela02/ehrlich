import { createFileRoute } from "@tanstack/react-router";
import { PromptInput, InvestigationList } from "@/features/investigation/components";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: investigations } = useInvestigations();

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-8">
      <div className="space-y-2 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Ehrlich</h1>
        <p className="text-muted-foreground">
          AI-powered antimicrobial discovery agent
        </p>
      </div>
      <PromptInput />
      {investigations && investigations.length > 0 && (
        <InvestigationList investigations={investigations} />
      )}
    </div>
  );
}

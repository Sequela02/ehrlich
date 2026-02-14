import { createFileRoute } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useInvestigationDetail } from "@/features/investigation/hooks/use-investigation-detail";
import { InvestigationComparison } from "@/features/investigation/components/InvestigationComparison";

export const Route = createFileRoute("/compare/$id1/$id2")({
  component: ComparePage,
});

function ComparePage() {
  const { id1, id2 } = Route.useParams();
  const queryA = useInvestigationDetail(id1);
  const queryB = useInvestigationDetail(id2);

  const loading = queryA.isLoading || queryB.isLoading;
  const error = queryA.error || queryB.error;

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-background px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3">
          <a
            href="/"
            className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </a>
          <div>
            <h1 className="text-xl font-semibold">Comparative Analysis</h1>
            <p className="font-mono text-[11px] text-muted-foreground">
              {id1.slice(0, 8)} vs {id2.slice(0, 8)}
            </p>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1200px] p-4 lg:p-6">
        {loading && (
          <p className="text-sm text-muted-foreground">Loading investigations...</p>
        )}
        {error && (
          <p className="text-sm text-destructive">
            Failed to load investigations: {error.message}
          </p>
        )}
        {queryA.data && queryB.data && (
          <InvestigationComparison invA={queryA.data} invB={queryB.data} />
        )}
      </main>
    </div>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/shared/components/layout/PageHeader";
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
      <PageHeader
        title="Comparative Analysis"
        subtitle={`${id1.slice(0, 8)} vs ${id2.slice(0, 8)}`}
        backTo="/"
      />
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

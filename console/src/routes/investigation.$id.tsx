import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/investigation/$id")({
  component: InvestigationPage,
});

function InvestigationPage() {
  const { id } = Route.useParams();
  return (
    <div className="mx-auto max-w-6xl p-8">
      <h1 className="text-2xl font-bold">Investigation {id}</h1>
      <p className="text-muted-foreground">Timeline and results will appear here.</p>
    </div>
  );
}

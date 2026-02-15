import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState, Suspense } from "react";
import Markdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { Download, Loader2 } from "lucide-react";
import { apiFetch } from "@/shared/lib/api";
import { getVizComponent, type VizPayload } from "@/features/visualization/VizRegistry";
import { VIZ_COLORS } from "@/features/visualization/theme";
import { PageHeader } from "@/shared/components/layout/PageHeader";

export const Route = createFileRoute("/paper/$id")({
  component: PaperPage,
});

interface PaperResponse {
  title: string;
  abstract: string;
  introduction: string;
  methods: string;
  results: string;
  discussion: string;
  references: string;
  supplementary: string;
  full_markdown: string;
  visualizations: VizPayload[];
}

const SECTION_ORDER = [
  "title",
  "abstract",
  "introduction",
  "methods",
  "results",
  "discussion",
  "references",
  "supplementary",
] as const;

function PaperPage() {
  const { id } = Route.useParams();
  const [paper, setPaper] = useState<PaperResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiFetch<PaperResponse>(`/investigate/${id}/paper`)
      .then((data) => {
        if (!cancelled) setPaper(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? "Failed to load paper");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-sm text-destructive">{error ?? "Paper not found"}</p>
        <Link
          to="/investigation/$id"
          params={{ id }}
          className="text-xs text-primary underline"
        >
          Back to investigation
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Toolbar -- hidden when printing */}
      <PageHeader
        title={paper.title}
        backTo={`/investigation/${id}`}
        className="no-print sticky top-0 z-10 backdrop-blur-sm bg-background/95"
        rightContent={
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
          >
            <Download className="h-3.5 w-3.5" />
            Download PDF
          </button>
        }
      />

      {/* Paper content */}
      <article className="mx-auto max-w-[900px] px-6 py-10">
        <div className="space-y-8">
          {SECTION_ORDER.map((key) => {
            const content = paper[key];
            if (!content) return null;
            return (
              <section key={key} className="paper-section">
                <div className="prose prose-sm prose-invert max-w-none prose-headings:text-foreground prose-a:text-primary prose-strong:text-foreground prose-code:text-primary prose-pre:rounded-lg prose-pre:border prose-pre:border-border prose-pre:bg-muted prose-table:text-xs prose-th:text-left prose-th:font-mono prose-th:text-[10px] prose-th:uppercase prose-th:tracking-wider prose-th:text-muted-foreground">
                  <Markdown rehypePlugins={[rehypeSanitize]}>{content}</Markdown>
                </div>
              </section>
            );
          })}

          {/* Figures: rendered visualizations */}
          {paper.visualizations.length > 0 && (
            <section className="paper-section space-y-6">
              <h2 className="text-lg font-semibold">Figures</h2>
              {paper.visualizations.map((viz, i) => (
                <VizFigure key={`${viz.viz_type}-${i}`} payload={viz} index={i + 1} />
              ))}
            </section>
          )}
        </div>
      </article>
    </div>
  );
}

function VizFigure({ payload, index }: { payload: VizPayload; index: number }) {
  const Component = getVizComponent(payload.viz_type);
  if (!Component) return null;

  return (
    <figure className="viz-figure space-y-2">
      <div
        className="rounded-md border border-border p-4"
        style={{ background: VIZ_COLORS.background }}
      >
        <Suspense
          fallback={
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          }
        >
          <Component data={payload.data} title={payload.title} />
        </Suspense>
      </div>
      <figcaption className="text-center font-mono text-[10px] text-muted-foreground">
        Figure {index}. {payload.title}
      </figcaption>
    </figure>
  );
}

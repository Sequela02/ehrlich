import { createFileRoute } from "@tanstack/react-router";
import { useRef, useEffect, useState, useMemo } from "react";
import { ArrowLeft, WifiOff } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import {
  Timeline,
  CandidateTable,
  ReportViewer,
  CostBadge,
  HypothesisBoard,
  ActiveExperimentCard,
  CompletionSummaryCard,
  NegativeControlPanel,
  LiveLabViewer,
  InvestigationDiagram,
} from "@/features/investigation/components";
import { FindingsPanel } from "@/features/investigation/components/FindingsPanel";
import { useSSE } from "@/features/investigation/hooks/use-sse";
import type { HypothesisNode, ExperimentNode, FindingNode } from "@/features/investigation/lib/diagram-builder";

export const Route = createFileRoute("/investigation/$id")({
  component: InvestigationPage,
});

type ViewTab = "timeline" | "lab" | "diagram";

function InvestigationPage() {
  const { id } = Route.useParams();
  const streamUrl = `/api/v1/investigate/${id}/stream`;
  const {
    events,
    connected,
    reconnecting,
    completed,
    hypotheses,
    currentHypothesisId,
    currentExperimentId,
    experiments,
    negativeControls,
    findings,
    candidates,
    summary,
    cost,
    error,
    activeToolName,
    experimentToolCount,
    experimentFindingCount,
  } = useSSE(streamUrl);

  const [activeTab, setActiveTab] = useState<ViewTab>("timeline");
  const timelineEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeTab === "timeline") {
      timelineEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [events.length, activeTab]);

  const currentExperiment = experiments.find((e) => e.id === currentExperimentId);
  const linkedHypothesis = hypotheses.find((h) => h.id === currentHypothesisId);

  const diagramHypotheses: HypothesisNode[] = useMemo(
    () =>
      hypotheses.map((h) => ({
        id: h.id,
        statement: h.statement,
        status: h.status,
        parentId: h.parent_id || undefined,
        confidence: h.confidence,
      })),
    [hypotheses],
  );

  const diagramExperiments: ExperimentNode[] = useMemo(
    () =>
      experiments.map((e) => ({
        id: e.id,
        hypothesisId: e.hypothesis_id,
        description: e.description,
        status: e.status as ExperimentNode["status"],
      })),
    [experiments],
  );

  const diagramFindings: FindingNode[] = useMemo(
    () =>
      findings.map((f, i) => ({
        id: `finding-${i}`,
        hypothesisId: f.hypothesis_id,
        summary: f.title,
        evidenceType: f.evidence_type,
      })),
    [findings],
  );

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a
            href="/"
            className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </a>
          <div>
            <h1 className="text-xl font-semibold">Investigation</h1>
            <p className="font-mono text-[11px] text-muted-foreground">{id}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusIndicator
            connected={connected}
            reconnecting={reconnecting}
            completed={completed}
            error={error}
          />
          <CostBadge cost={cost} />
        </div>
      </div>

      <div className="mb-6">
        <HypothesisBoard
          hypotheses={hypotheses}
          currentHypothesisId={currentHypothesisId}
        />
      </div>

      <div className="mb-6">
        {completed ? (
          <CompletionSummaryCard
            candidateCount={candidates.length}
            findingCount={findings.length}
            hypothesisCount={hypotheses.length}
          />
        ) : (
          <ActiveExperimentCard
            completed={completed}
            currentExperimentId={currentExperimentId}
            experimentDescription={currentExperiment?.description}
            linkedHypothesis={linkedHypothesis}
            activeToolName={activeToolName}
            experimentToolCount={experimentToolCount}
            experimentFindingCount={experimentFindingCount}
          />
        )}
      </div>

      <div className="mb-4 flex gap-1 rounded-lg border border-border bg-muted/30 p-1">
        {(["timeline", "lab", "diagram"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "rounded-md px-4 py-1.5 font-mono text-[11px] font-medium uppercase tracking-wider transition-colors",
              activeTab === tab
                ? "bg-surface text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {tab === "timeline" ? "Timeline" : tab === "lab" ? "Lab View" : "Diagram"}
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {activeTab === "timeline" && (
          <section>
            <div className="max-h-[500px] overflow-y-auto rounded-lg border border-border bg-surface p-4">
              <Timeline events={events} />
              <div ref={timelineEndRef} />
            </div>
          </section>
        )}

        {activeTab === "lab" && (
          <section>
            <LiveLabViewer events={events} completed={completed} />
          </section>
        )}

        {activeTab === "diagram" && (
          <section>
            <InvestigationDiagram
              hypotheses={diagramHypotheses}
              experiments={diagramExperiments}
              findings={diagramFindings}
              completed={completed}
            />
          </section>
        )}

        <section>
          <FindingsPanel findings={findings} />
        </section>

        {negativeControls.length > 0 && (
          <section>
            <NegativeControlPanel controls={negativeControls} />
          </section>
        )}

        {candidates.length > 0 && (
          <section>
            <CandidateTable candidates={candidates} />
          </section>
        )}

        {completed && summary && (
          <section>
            <h2 className="mb-3 border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Report
            </h2>
            <div className="rounded-lg border border-border bg-surface p-6">
              <ReportViewer content={summary} />
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function StatusIndicator({
  connected,
  reconnecting,
  completed,
  error,
}: {
  connected: boolean;
  reconnecting: boolean;
  completed: boolean;
  error: string | null;
}) {
  if (error) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-destructive">
        <span className="h-2 w-2 rounded-full bg-destructive" />
        Error
      </span>
    );
  }
  if (completed) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-secondary">
        <span className="h-2 w-2 rounded-full bg-secondary" />
        Completed
      </span>
    );
  }
  if (reconnecting) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-accent">
        <WifiOff className="h-3 w-3 animate-pulse" />
        Reconnecting...
      </span>
    );
  }
  if (connected) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-primary">
        <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
        Running
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className="h-2 w-2 rounded-full bg-muted-foreground" />
      Connecting
    </span>
  );
}

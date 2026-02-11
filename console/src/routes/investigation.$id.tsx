import { createFileRoute } from "@tanstack/react-router";
import { useRef, useEffect, useState, useMemo } from "react";
import { ArrowLeft, PanelRightClose, PanelRightOpen, WifiOff } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { ErrorBoundary } from "@/features/shared/components/ErrorBoundary";
import {
  Timeline,
  CandidateTable,
  CostBadge,
  HypothesisBoard,
  ActiveExperimentCard,
  CompletionSummaryCard,
  NegativeControlPanel,
  LiveLabViewer,
  InvestigationDiagram,
} from "@/features/investigation/components";
import { FindingsPanel } from "@/features/investigation/components/FindingsPanel";
import { InvestigationReport } from "@/features/investigation/components/InvestigationReport";
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
    prompt,
    cost,
    error,
    activeToolName,
    experimentToolCount,
    experimentFindingCount,
  } = useSSE(streamUrl);

  const [activeTab, setActiveTab] = useState<ViewTab>("lab");
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const sidebarTimelineRef = useRef<HTMLDivElement>(null);
  const mobileTimelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    for (const ref of [sidebarTimelineRef, mobileTimelineRef]) {
      const el = ref.current;
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, [events.length]);

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
    <div className="flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      {/* Header */}
      <header className="shrink-0 border-b border-border bg-background px-4 py-3 lg:px-6">
        <div className="flex items-center justify-between">
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
            <button
              onClick={() => setSidebarOpen((p) => !p)}
              className="hidden rounded-md p-1.5 text-muted-foreground transition-colors hover:text-foreground lg:inline-flex"
              title={sidebarOpen ? "Hide timeline" : "Show timeline"}
            >
              {sidebarOpen ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Experiment status bar */}
      <div className="shrink-0 border-b border-border px-4 py-2 lg:px-6">
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

      {/* Split pane: left content + right timeline sidebar */}
      <div className="flex flex-1 flex-col lg:min-h-0 lg:flex-row">
        {/* Left panel */}
        <main className="flex-1 space-y-6 p-4 lg:min-w-0 lg:overflow-y-auto lg:p-6">
          {/* --- LIVE VIEW: show components as they build up --- */}
          {!completed && (
            <>
              <HypothesisBoard
                hypotheses={hypotheses}
                currentHypothesisId={currentHypothesisId}
              />

              {/* Tab bar */}
              <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1">
                <button
                  onClick={() => setActiveTab("timeline")}
                  className={cn(
                    "rounded-md px-4 py-1.5 font-mono text-[11px] font-medium uppercase tracking-wider transition-colors lg:hidden",
                    activeTab === "timeline"
                      ? "bg-surface text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  Timeline
                </button>
                {(["lab", "diagram"] as const).map((tab) => (
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
                    {tab === "lab" ? "Lab View" : "Diagram"}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {activeTab === "timeline" && (
                <section className="lg:hidden">
                  <div
                    ref={mobileTimelineRef}
                    className="max-h-[500px] overflow-y-auto rounded-lg border border-border bg-surface p-4"
                  >
                    <Timeline events={events} />
                  </div>
                </section>
              )}

              {activeTab === "lab" && (
                <section className="space-y-2">
                  <div>
                    <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      Lab View
                    </h3>
                    <p className="mt-1 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
                      Real-time 3D visualization of molecules as they are analyzed. Proteins, ligands, and scores appear as tools process them.
                    </p>
                  </div>
                  <ErrorBoundary fallbackMessage="Failed to load 3D viewer">
                    <LiveLabViewer
                      events={events}
                      completed={completed}
                      experiments={experiments}
                      activeExperimentId={activeExperimentId}
                      onExperimentChange={setActiveExperimentId}
                    />
                  </ErrorBoundary>
                </section>
              )}

              {activeTab === "diagram" && (
                <section className="space-y-2">
                  <div>
                    <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      Investigation Diagram
                    </h3>
                    <p className="mt-1 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
                      Visual map of hypothesis-experiment-finding relationships. Scroll to zoom, drag to pan.
                    </p>
                  </div>
                  <ErrorBoundary fallbackMessage="Failed to load investigation diagram">
                    <InvestigationDiagram
                      hypotheses={diagramHypotheses}
                      experiments={diagramExperiments}
                      findings={diagramFindings}
                    />
                  </ErrorBoundary>
                </section>
              )}

              <section>
                <FindingsPanel findings={findings} />
              </section>

              {candidates.length > 0 && (
                <section>
                  <CandidateTable candidates={candidates} />
                </section>
              )}

              {negativeControls.length > 0 && (
                <section>
                  <NegativeControlPanel controls={negativeControls} />
                </section>
              )}
            </>
          )}

          {/* --- COMPLETED VIEW: structured report following scientific workflow --- */}
          {completed && (
            <>
              {/* Visual exploration tabs (Lab + Diagram) */}
              <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1">
                <button
                  onClick={() => setActiveTab("timeline")}
                  className={cn(
                    "rounded-md px-4 py-1.5 font-mono text-[11px] font-medium uppercase tracking-wider transition-colors lg:hidden",
                    activeTab === "timeline"
                      ? "bg-surface text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  Timeline
                </button>
                {(["lab", "diagram"] as const).map((tab) => (
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
                    {tab === "lab" ? "Lab View" : "Diagram"}
                  </button>
                ))}
              </div>

              {activeTab === "timeline" && (
                <section className="lg:hidden">
                  <div
                    ref={mobileTimelineRef}
                    className="max-h-[500px] overflow-y-auto rounded-lg border border-border bg-surface p-4"
                  >
                    <Timeline events={events} />
                  </div>
                </section>
              )}

              {activeTab === "lab" && (
                <section className="space-y-2">
                  <div>
                    <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      Lab View
                    </h3>
                    <p className="mt-1 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
                      3D molecular scene from the investigation. Proteins, ligands, and docking scores visualized in real-time during the experiment.
                    </p>
                  </div>
                  <ErrorBoundary fallbackMessage="Failed to load 3D viewer">
                    <LiveLabViewer
                      events={events}
                      completed={completed}
                      experiments={experiments}
                      activeExperimentId={activeExperimentId}
                      onExperimentChange={setActiveExperimentId}
                    />
                  </ErrorBoundary>
                </section>
              )}

              {activeTab === "diagram" && (
                <section className="space-y-2">
                  <div>
                    <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      Investigation Diagram
                    </h3>
                    <p className="mt-1 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
                      Visual map of hypothesis-experiment-finding relationships. Scroll to zoom, drag to pan.
                    </p>
                  </div>
                  <ErrorBoundary fallbackMessage="Failed to load investigation diagram">
                    <InvestigationDiagram
                      hypotheses={diagramHypotheses}
                      experiments={diagramExperiments}
                      findings={diagramFindings}
                    />
                  </ErrorBoundary>
                </section>
              )}

              {/* Structured report: follows scientific method workflow */}
              <InvestigationReport
                prompt={prompt}
                summary={summary}
                hypotheses={hypotheses}
                experiments={experiments}
                findings={findings}
                candidates={candidates}
                negativeControls={negativeControls}
                cost={cost}
              />
            </>
          )}
        </main>

        {/* Right panel: timeline sidebar (desktop only) */}
        <aside
          className={cn(
            "hidden shrink-0 flex-col border-l border-border lg:flex",
            sidebarOpen ? "w-80" : "w-0 overflow-hidden border-l-0",
          )}
          style={{ transition: "width 200ms ease, border 200ms ease" }}
        >
          <div className="shrink-0 border-b border-border px-4 py-2.5">
            <div className="flex items-center justify-between">
              <h3 className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Timeline
              </h3>
              <span className="font-mono text-[10px] tabular-nums text-muted-foreground/50">
                {events.length} events
              </span>
            </div>
            <p className="mt-1 text-[10px] leading-relaxed text-muted-foreground/40">
              {completed
                ? "Full audit trail replayed from stored events."
                : "Live feed of tool calls, results, and decisions."}
            </p>
          </div>
          <div
            ref={sidebarTimelineRef}
            className="flex-1 overflow-y-auto p-3"
          >
            <Timeline events={events} />
          </div>
        </aside>
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

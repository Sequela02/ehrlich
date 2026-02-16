import { createFileRoute, Link } from "@tanstack/react-router";
import { useRef, useEffect, useState, useMemo, useCallback } from "react";
import { AlertCircle, Ban, ChevronDown, ExternalLink, Home, Loader2, PanelRightClose, PanelRightOpen, WifiOff } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";
import { apiFetch } from "@/shared/lib/api";
import { ErrorBoundary } from "@/features/shared/components/ErrorBoundary";
import {
  Timeline,
  CostBadge,
  HypothesisBoard,
  ActiveExperimentCard,
  NegativeControlPanel,
  InvestigationDiagram,
  PhaseProgress,
  PhaseSection,
  LiteratureSurveyCard,
  ClassificationCard,
} from "@/features/investigation/components";
import { HypothesisApprovalCard } from "@/features/investigation/components/HypothesisApprovalCard";
import { FindingsPanel } from "@/features/investigation/components/FindingsPanel";
import { InvestigationReport } from "@/features/investigation/components/InvestigationReport";
import { useSSE } from "@/features/investigation/hooks/use-sse";
import { useInvestigationDetail } from "@/features/investigation/hooks/use-investigation-detail";
import type { HypothesisNode, ExperimentNode, FindingNode } from "@/features/investigation/lib/diagram-builder";
import VisualizationPanel from "@/features/visualization/VisualizationPanel";

export const Route = createFileRoute("/investigation/$id")({
  component: InvestigationPage,
});

function InvestigationPage() {
  const { id } = Route.useParams();
  const streamUrl = `/investigate/${id}/stream`;
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
    positiveControls,
    findings,
    candidates,
    summary,
    prompt,
    cost,
    currentPhase,
    approvalPending,
    pendingApprovalHypotheses,
    domainConfig,
    literatureSurvey,
    validationMetrics,
    error,
    activeToolName,
    experimentToolCount,
    experimentFindingCount,
    visualizations,
    diagramUrl,
  } = useSSE(streamUrl);

  const { data: detail } = useInvestigationDetail(id);
  const investigationPrompt = prompt || detail?.prompt || "";

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const sidebarTimelineRef = useRef<HTMLDivElement>(null);

  const isActive = connected && !completed && !error;

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      await apiFetch(`/investigate/${id}/cancel`, { method: "POST" });
      toast.info("Investigation cancelled");
    } catch {
      toast.error("Failed to cancel investigation");
      setCancelling(false);
    }
  }, [id]);

  useEffect(() => {
    const el = sidebarTimelineRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [events.length]);

  const currentExperiment = experiments.find((e) => e.id === currentExperimentId);
  const linkedHypothesis = hypotheses.find((h) => h.id === currentHypothesisId);

  const phaseNumber = currentPhase?.phase ?? 0;
  const effectiveCurrentPhase = completed ? 7 : phaseNumber;

  const diagramHypotheses: HypothesisNode[] = useMemo(
    () =>
      hypotheses.map((h) => ({
        id: h.id,
        statement: h.statement,
        status: h.status,
        parentId: h.parent_id || undefined,
        confidence: h.confidence,
        rationale: h.rationale,
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
        tool_count: e.tool_count,
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
        detail: f.detail,
        source_id: f.source_id,
      })),
    [findings],
  );

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      {/* Header */}
      <PageHeader
        title={investigationPrompt || "Investigation"}
        titleMaxLength={60}
        subtitle={id}
        backTo="/"
        rightContent={
          <div className="flex items-center gap-3">
            {domainConfig && (
              <Badge variant="outline" className="hidden text-[10px] sm:inline-flex">
                {domainConfig.display_name}
              </Badge>
            )}
            <StatusIndicator
              connected={connected}
              reconnecting={reconnecting}
              completed={completed}
              error={error}
            />
            <CostBadge cost={cost} />
            {isActive && (
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className="inline-flex items-center gap-1.5 rounded-sm border border-destructive/30 px-2.5 py-1.5 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:opacity-50"
              >
                <Ban className="h-3 w-3" />
                {cancelling ? "Cancelling..." : "Cancel"}
              </button>
            )}
            <button
              onClick={() => setSidebarOpen((p) => !p)}
              className="hidden rounded-md p-1.5 text-muted-foreground transition-colors hover:text-foreground lg:inline-flex"
              title={sidebarOpen ? "Hide timeline" : "Show timeline"}
              aria-label={sidebarOpen ? "Hide timeline" : "Show timeline"}
            >
              {sidebarOpen ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
            </button>
          </div>
        }
      />

      {/* Phase progress bar */}
      <PhaseProgress phase={currentPhase} completed={completed} />

      {/* Split pane: left content + right timeline sidebar */}
      <div className="flex flex-1 flex-col lg:min-h-0 lg:flex-row">
        {/* Left panel */}
        <main className="flex-1 space-y-4 p-4 lg:min-w-0 lg:overflow-y-auto lg:p-6">
          {/* Error state */}
          {error && (
            <ErrorState error={error} investigationId={id} hasPartialResults={phaseNumber > 1} />
          )}

          {/* Loading state -- before any phase starts and no error */}
          {!error && !completed && phaseNumber === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                {connected ? "Initializing investigation..." : "Connecting to investigation stream..."}
              </p>
            </div>
          )}

          {/* Phase 1: Classification */}
          <PhaseSection
            phaseNumber={1}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Classification"
            summaryContent={domainConfig?.display_name ?? "Classified"}
          >
            <ClassificationCard domainConfig={domainConfig} />
          </PhaseSection>

          {/* Phase 2: Literature Survey */}
          <PhaseSection
            phaseNumber={2}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Literature Survey"
            summaryContent={
              literatureSurvey
                ? `${literatureSurvey.included_results}/${literatureSurvey.total_results} papers · ${literatureSurvey.evidence_grade} grade`
                : "Surveyed"
            }
          >
            {literatureSurvey ? (
              <LiteratureSurveyCard data={literatureSurvey} />
            ) : (
              <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary/40" />
                Searching literature...
              </div>
            )}
          </PhaseSection>

          {/* Phase 3: Formulation */}
          <PhaseSection
            phaseNumber={3}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Formulation"
            summaryContent={`${hypotheses.length} hypothes${hypotheses.length === 1 ? "is" : "es"} formulated`}
          >
            {approvalPending ? (
              <HypothesisApprovalCard
                investigationId={id}
                hypotheses={pendingApprovalHypotheses}
                onApproved={() => { }}
              />
            ) : (
              <HypothesisBoard
                hypotheses={hypotheses}
                currentHypothesisId={currentHypothesisId}
              />
            )}
          </PhaseSection>

          {/* Phase 4: Hypothesis Testing */}
          <PhaseSection
            phaseNumber={4}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Hypothesis Testing"
            summaryContent={`${experiments.length} experiment${experiments.length === 1 ? "" : "s"} · ${findings.length} finding${findings.length === 1 ? "" : "s"}`}
          >
            <div className="space-y-6">
              <ActiveExperimentCard
                completed={completed}
                currentExperimentId={currentExperimentId}
                experimentDescription={currentExperiment?.description}
                linkedHypothesis={linkedHypothesis}
                activeToolName={activeToolName}
                experimentToolCount={experimentToolCount}
                experimentFindingCount={experimentFindingCount}
                currentExperiment={currentExperiment}
              />

              <HypothesisBoard
                hypotheses={hypotheses}
                currentHypothesisId={currentHypothesisId}
              />

              <ErrorBoundary fallbackMessage="Failed to load investigation diagram">
                <InvestigationDiagram
                  hypotheses={diagramHypotheses}
                  experiments={diagramExperiments}
                  findings={diagramFindings}
                />
              </ErrorBoundary>

              <VisualizationPanel
                visualizations={visualizations}
                events={events}
                experiments={experiments}
                completed={completed}
              />

              <FindingsPanel findings={findings} />
            </div>
          </PhaseSection>

          {/* Phase 5: Controls */}
          <PhaseSection
            phaseNumber={5}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Controls"
            summaryContent={
              validationMetrics
                ? `${negativeControls.length + positiveControls.length} controls · Z'=${validationMetrics.z_prime?.toFixed(2) ?? "N/A"}`
                : `${negativeControls.length + positiveControls.length} controls`
            }
          >
            <NegativeControlPanel controls={negativeControls} />
          </PhaseSection>

          {/* Phase 6: Synthesis */}
          <PhaseSection
            phaseNumber={6}
            currentPhase={effectiveCurrentPhase}
            completed={completed}
            title="Synthesis"
            summaryContent={`${candidates.length} candidate${candidates.length === 1 ? "" : "s"} identified`}
            defaultExpanded
          >
            <div className="space-y-6">
              <InvestigationReport
                investigationId={id}
                prompt={prompt}
                summary={summary}
                hypotheses={hypotheses}
                experiments={experiments}
                findings={findings}
                candidates={candidates}
                negativeControls={negativeControls}
                cost={cost}
                domainConfig={domainConfig}
                validationMetrics={validationMetrics}
              />

              {diagramUrl && (
                <a
                  href={diagramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-sm border border-primary/30 bg-primary/5 px-4 py-2.5 font-mono text-xs font-medium text-primary transition-colors hover:bg-primary/10"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View Visual Summary
                </a>
              )}
            </div>
          </PhaseSection>
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

function ErrorState({
  error,
  investigationId,
  hasPartialResults,
}: {
  error: string;
  investigationId: string;
  hasPartialResults: boolean;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  return (
    <div className="flex flex-col items-center gap-6 py-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="h-7 w-7 text-destructive" />
      </div>

      <div className="max-w-md space-y-2">
        <h2 className="text-lg font-semibold text-foreground">
          Something went wrong
        </h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {hasPartialResults
            ? "The investigation encountered an error before it could finish. Partial results from completed phases are shown below."
            : "The investigation could not be completed. This can happen due to a temporary service issue or an invalid research prompt."}
        </p>
      </div>

      <Link
        to="/"
        className="inline-flex items-center gap-2 rounded-sm bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
      >
        <Home className="h-3.5 w-3.5" />
        Start New Investigation
      </Link>

      <button
        onClick={() => setDetailsOpen((p) => !p)}
        className="inline-flex items-center gap-1 text-[11px] text-muted-foreground/50 transition-colors hover:text-muted-foreground"
      >
        Technical details
        <ChevronDown className={`h-3 w-3 transition-transform ${detailsOpen ? "rotate-180" : ""}`} />
      </button>

      {detailsOpen && (
        <div className="w-full max-w-lg rounded-md border border-border bg-muted/30 p-3 text-left">
          <p className="font-mono text-[11px] text-muted-foreground/70 break-all">
            {error}
          </p>
          <p className="mt-2 font-mono text-[10px] text-muted-foreground/40">
            Investigation ID: {investigationId}
          </p>
        </div>
      )}
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

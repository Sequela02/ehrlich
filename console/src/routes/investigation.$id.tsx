import { createFileRoute } from "@tanstack/react-router";
import { useRef, useEffect } from "react";
import { ArrowLeft, WifiOff } from "lucide-react";
import {
  Timeline,
  CandidateTable,
  ReportViewer,
  CostBadge,
  PhaseProgress,
  ActivePhaseCard,
} from "@/features/investigation/components";
import { FindingsPanel } from "@/features/investigation/components/FindingsPanel";
import { useSSE } from "@/features/investigation/hooks/use-sse";

export const Route = createFileRoute("/investigation/$id")({
  component: InvestigationPage,
});

function InvestigationPage() {
  const { id } = Route.useParams();
  const streamUrl = `/api/v1/investigate/${id}/stream`;
  const {
    events,
    connected,
    reconnecting,
    completed,
    currentPhase,
    completedPhases,
    findings,
    candidates,
    summary,
    cost,
    error,
    activeToolName,
    phaseToolCount,
    phaseFindingCount,
  } = useSSE(streamUrl);

  const timelineEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

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
        <PhaseProgress
          currentPhase={currentPhase}
          completedPhases={completedPhases}
        />
      </div>

      <div className="mb-6">
        <ActivePhaseCard
          currentPhase={currentPhase}
          completed={completed}
          activeToolName={activeToolName}
          phaseToolCount={phaseToolCount}
          phaseFindingCount={phaseFindingCount}
        />
      </div>

      <div className="space-y-6">
        <section>
          <h2 className="mb-3 border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Timeline
          </h2>
          <div className="max-h-[500px] overflow-y-auto rounded-lg border border-border bg-surface p-4">
            <Timeline events={events} />
            <div ref={timelineEndRef} />
          </div>
        </section>

        <section>
          <FindingsPanel findings={findings} />
        </section>

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

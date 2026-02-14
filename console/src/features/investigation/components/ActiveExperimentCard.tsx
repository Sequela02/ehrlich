import { FlaskConical, ShieldCheck, Wrench } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { Experiment, Hypothesis } from "../types";

interface ActiveExperimentCardProps {
  completed: boolean;
  currentExperimentId: string;
  experimentDescription?: string;
  linkedHypothesis?: Hypothesis;
  activeToolName: string;
  experimentToolCount: number;
  experimentFindingCount: number;
  currentExperiment?: Experiment;
}

export function ActiveExperimentCard({
  completed,
  currentExperimentId,
  experimentDescription,
  linkedHypothesis,
  activeToolName,
  experimentToolCount,
  experimentFindingCount,
  currentExperiment,
}: ActiveExperimentCardProps) {
  if (completed) return null;

  if (!currentExperimentId) {
    return (
      <div className="relative overflow-hidden rounded-md border border-accent/30 bg-accent/5 p-4">
        <div className="absolute inset-0 animate-pulse rounded-md border border-accent/20" />
        <div className="relative flex items-center gap-3">
          <FlaskConical className="h-5 w-5 animate-pulse text-accent" />
          <div>
            <p className="text-sm font-medium text-accent">
              Preparing next experiment...
            </p>
            <p className="text-xs text-muted-foreground">
              {linkedHypothesis
                ? `Evaluating hypothesis: ${linkedHypothesis.statement.slice(0, 80)}...`
                : "Formulating hypotheses..."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const iv = currentExperiment?.independent_variable;
  const dv = currentExperiment?.dependent_variable;
  const controlCount = currentExperiment?.controls?.length ?? 0;

  return (
    <div className="relative overflow-hidden rounded-md border border-primary/30 bg-primary/5 p-4">
      <div className="absolute inset-0 animate-pulse rounded-md border border-primary/10" />
      <div className="relative flex flex-col gap-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <FlaskConical className="h-5 w-5 text-primary" />
            <div>
              <p className="text-sm font-medium text-primary">
                {experimentDescription
                  ? experimentDescription.slice(0, 80)
                  : "Running experiment..."}
              </p>
              {activeToolName ? (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Wrench className="h-3 w-3 animate-spin text-primary/60" />
                  <span className="font-mono">{activeToolName}</span>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">Processing...</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span
              className={cn(
                "font-mono tabular-nums",
                experimentToolCount > 0 && "text-primary/70",
              )}
            >
              {experimentToolCount} {experimentToolCount === 1 ? "tool" : "tools"}
            </span>
            <span className="text-border">|</span>
            <span
              className={cn(
                "font-mono tabular-nums",
                experimentFindingCount > 0 && "text-primary/70",
              )}
            >
              {experimentFindingCount}{" "}
              {experimentFindingCount === 1 ? "finding" : "findings"}
            </span>
          </div>
        </div>
        {(iv || dv || controlCount > 0) && (
          <div className="flex flex-wrap items-center gap-2 pl-8 text-xs text-muted-foreground">
            {iv && dv && (
              <span>
                Testing: <span className="font-medium text-foreground/70">{iv}</span>
                {" \u2192 "}
                <span className="font-medium text-foreground/70">{dv}</span>
              </span>
            )}
            {controlCount > 0 && (
              <span className="inline-flex items-center gap-1 rounded bg-primary/10 px-1.5 py-0.5 text-primary/80">
                <ShieldCheck className="h-3 w-3" />
                {controlCount} {controlCount === 1 ? "control" : "controls"}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

import { FlaskConical, Wrench } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { Hypothesis } from "../types";

interface ActiveExperimentCardProps {
  completed: boolean;
  currentExperimentId: string;
  experimentDescription?: string;
  linkedHypothesis?: Hypothesis;
  activeToolName: string;
  experimentToolCount: number;
  experimentFindingCount: number;
}

export function ActiveExperimentCard({
  completed,
  currentExperimentId,
  experimentDescription,
  linkedHypothesis,
  activeToolName,
  experimentToolCount,
  experimentFindingCount,
}: ActiveExperimentCardProps) {
  if (completed) return null;

  if (!currentExperimentId) {
    return (
      <div className="relative overflow-hidden rounded-lg border border-accent/30 bg-accent/5 p-4">
        <div className="absolute inset-0 animate-pulse rounded-lg border border-accent/20" />
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

  return (
    <div className="relative overflow-hidden rounded-lg border border-primary/30 bg-primary/5 p-4">
      <div className="absolute inset-0 animate-pulse rounded-lg border border-primary/10" />
      <div className="relative flex items-center justify-between gap-4">
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
    </div>
  );
}

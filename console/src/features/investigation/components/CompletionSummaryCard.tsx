import { CheckCircle2, FlaskConical, Lightbulb, TestTube } from "lucide-react";

interface CompletionSummaryCardProps {
  candidateCount: number;
  findingCount: number;
  hypothesisCount: number;
}

export function CompletionSummaryCard({
  candidateCount,
  findingCount,
  hypothesisCount,
}: CompletionSummaryCardProps) {
  return (
    <div className="relative overflow-hidden rounded-lg border border-primary/30 bg-primary/5 p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-primary" />
          <p className="text-sm font-medium text-primary">
            Investigation Complete
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1 font-mono tabular-nums text-primary/70">
            <TestTube className="h-3 w-3" />
            {hypothesisCount} {hypothesisCount === 1 ? "hypothesis" : "hypotheses"}
          </span>
          <span className="text-border">|</span>
          <span className="inline-flex items-center gap-1 font-mono tabular-nums text-primary/70">
            <FlaskConical className="h-3 w-3" />
            {candidateCount} {candidateCount === 1 ? "candidate" : "candidates"}
          </span>
          <span className="text-border">|</span>
          <span className="inline-flex items-center gap-1 font-mono tabular-nums text-primary/70">
            <Lightbulb className="h-3 w-3" />
            {findingCount} {findingCount === 1 ? "finding" : "findings"}
          </span>
        </div>
      </div>
    </div>
  );
}

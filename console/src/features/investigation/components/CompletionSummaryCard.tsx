import { useState } from "react";
import { CheckCircle2, ChevronDown, FlaskConical, Lightbulb, TestTube } from "lucide-react";
import type { CostInfo } from "../types";

interface CompletionSummaryCardProps {
  candidateCount: number;
  findingCount: number;
  hypothesisCount: number;
  cost?: CostInfo | null;
}

export function CompletionSummaryCard({
  candidateCount,
  findingCount,
  hypothesisCount,
  cost,
}: CompletionSummaryCardProps) {
  const [expanded, setExpanded] = useState(false);

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
          {cost && (
            <>
              <span className="text-border">|</span>
              <button
                onClick={() => setExpanded(!expanded)}
                className="inline-flex items-center gap-1 font-mono tabular-nums text-primary/70 transition-colors hover:text-primary"
              >
                ${cost.totalCost.toFixed(4)}
                <ChevronDown className={`h-3 w-3 transition-transform ${expanded ? "rotate-180" : ""}`} />
              </button>
            </>
          )}
        </div>
      </div>

      {expanded && cost?.byModel && (
        <div className="mt-3 border-t border-primary/10 pt-3">
          <div className="grid grid-cols-4 gap-2 font-mono text-[10px] text-muted-foreground">
            <span className="font-medium uppercase tracking-wider">Model</span>
            <span className="text-right font-medium uppercase tracking-wider">Input</span>
            <span className="text-right font-medium uppercase tracking-wider">Output</span>
            <span className="text-right font-medium uppercase tracking-wider">Cost</span>
            {Object.entries(cost.byModel).map(([model, data]) => {
              const shortName = model.includes("opus")
                ? "Director (Opus)"
                : model.includes("sonnet")
                  ? "Researcher (Sonnet)"
                  : "Summarizer (Haiku)";
              return (
                <div key={model} className="col-span-4 grid grid-cols-4 gap-2">
                  <span className="truncate text-foreground/70">{shortName}</span>
                  <span className="text-right tabular-nums">{data.input_tokens.toLocaleString()}</span>
                  <span className="text-right tabular-nums">{data.output_tokens.toLocaleString()}</span>
                  <span className="text-right tabular-nums">${data.cost_usd.toFixed(4)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

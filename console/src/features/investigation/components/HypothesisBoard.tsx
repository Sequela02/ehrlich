import type { Hypothesis } from "../types";
import { HypothesisCard } from "./HypothesisCard";

interface HypothesisBoardProps {
  hypotheses: Hypothesis[];
  currentHypothesisId: string;
}

export function HypothesisBoard({
  hypotheses,
  currentHypothesisId,
}: HypothesisBoardProps) {
  if (hypotheses.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Hypotheses ({hypotheses.length})
      </h3>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {hypotheses.map((h) => (
          <div
            key={h.id}
            className={
              h.id === currentHypothesisId
                ? "ring-1 ring-accent/30 rounded-lg"
                : ""
            }
          >
            <HypothesisCard hypothesis={h} />
          </div>
        ))}
      </div>
    </div>
  );
}

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
      <div>
        <h3 className="border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
          Hypotheses ({hypotheses.length})
        </h3>
        <p className="mt-1 pl-4 text-xs leading-relaxed text-muted-foreground/50">
          Testable hypotheses formulated by the AI. Each is tested through experiments, then evaluated as supported, refuted, or revised.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {hypotheses.map((h) => (
          <div
            key={h.id}
            className={
              h.id === currentHypothesisId
                ? "ring-1 ring-accent/30 rounded-md"
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

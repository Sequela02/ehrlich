import { useState } from "react";
import type { CostInfo } from "../types";

interface CostBadgeProps {
  cost: CostInfo | null;
}

const MODEL_LABELS: Record<string, string> = {
  "claude-opus-4-6": "Director",
  "claude-sonnet-4-5-20250929": "Researcher",
  "claude-haiku-4-5-20251001": "Summarizer",
};

function modelLabel(model: string): string {
  return MODEL_LABELS[model] ?? model.split("-").slice(1, 3).join("-");
}

export function CostBadge({ cost }: CostBadgeProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);

  if (!cost) return null;

  return (
    <div className="relative">
      <button
        onClick={() =>
          cost.byModel ? setShowBreakdown((p) => !p) : undefined
        }
        className="inline-flex items-center gap-3 rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/20"
      >
        <span>{cost.inputTokens.toLocaleString()} in</span>
        <span className="text-border">|</span>
        <span>{cost.outputTokens.toLocaleString()} out</span>
        <span className="text-border">|</span>
        <span>{cost.toolCalls} tools</span>
        <span className="text-border">|</span>
        <span className="font-medium text-primary">
          ${cost.totalCost.toFixed(4)}
        </span>
      </button>
      {showBreakdown && cost.byModel && (
        <div className="absolute right-0 top-full z-10 mt-1 rounded-md border border-border bg-surface p-3 shadow-lg">
          <div className="space-y-1.5">
            {Object.entries(cost.byModel).map(([model, data]) => (
              <div
                key={model}
                className="flex items-center justify-between gap-6 text-xs"
              >
                <span className="font-mono text-muted-foreground">
                  {modelLabel(model)}
                </span>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-muted-foreground/60">
                    {data.calls} calls
                  </span>
                  <span className="text-primary">
                    ${data.cost_usd.toFixed(4)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

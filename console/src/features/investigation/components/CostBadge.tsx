import type { CostInfo } from "../types";

interface CostBadgeProps {
  cost: CostInfo | null;
}

export function CostBadge({ cost }: CostBadgeProps) {
  if (!cost) return null;

  return (
    <div className="inline-flex items-center gap-3 rounded-lg border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground">
      <span>{cost.inputTokens.toLocaleString()} in</span>
      <span className="text-border">|</span>
      <span>{cost.outputTokens.toLocaleString()} out</span>
      <span className="text-border">|</span>
      <span>{cost.toolCalls} tools</span>
      <span className="text-border">|</span>
      <span className="font-medium text-primary">${cost.totalCost.toFixed(4)}</span>
    </div>
  );
}

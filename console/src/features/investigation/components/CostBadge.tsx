import type { CostInfo } from "../types";

interface CostBadgeProps {
  cost: CostInfo | null;
}

export function CostBadge({ cost }: CostBadgeProps) {
  if (!cost) return null;

  return (
    <div className="inline-flex items-center gap-3 rounded-lg bg-muted px-3 py-1.5 text-xs text-muted-foreground">
      <span>{cost.inputTokens.toLocaleString()} in</span>
      <span className="text-muted-foreground/40">|</span>
      <span>{cost.outputTokens.toLocaleString()} out</span>
      <span className="text-muted-foreground/40">|</span>
      <span>{cost.toolCalls} tools</span>
      <span className="text-muted-foreground/40">|</span>
      <span className="font-medium">${cost.totalCost.toFixed(4)}</span>
    </div>
  );
}

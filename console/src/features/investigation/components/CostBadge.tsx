import type { CostInfo } from "../types";

interface CostBadgeProps {
  cost: CostInfo;
}

export function CostBadge({ cost }: CostBadgeProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-1.5 text-xs text-muted-foreground">
      <span>{cost.inputTokens.toLocaleString()} in</span>
      <span>{cost.outputTokens.toLocaleString()} out</span>
      <span>{cost.toolCalls} tools</span>
      <span className="font-medium">${cost.totalCost.toFixed(4)}</span>
    </div>
  );
}

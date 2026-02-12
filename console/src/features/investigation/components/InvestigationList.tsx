import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Clock, FlaskConical, AlertCircle, CheckCircle2, GitCompareArrows } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { InvestigationSummary } from "../types";

interface InvestigationListProps {
  investigations: InvestigationSummary[];
}

const STATUS_CONFIG: Record<
  string,
  { icon: typeof Clock; label: string; className: string }
> = {
  pending: {
    icon: Clock,
    label: "Pending",
    className: "text-muted-foreground",
  },
  running: {
    icon: FlaskConical,
    label: "Running",
    className: "text-primary",
  },
  completed: {
    icon: CheckCircle2,
    label: "Completed",
    className: "text-secondary",
  },
  failed: {
    icon: AlertCircle,
    label: "Failed",
    className: "text-destructive",
  },
};

export function InvestigationList({ investigations }: InvestigationListProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const navigate = useNavigate();
  const completed = investigations.filter((inv) => inv.status === "completed");

  if (investigations.length === 0) {
    return null;
  }

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < 2) {
        next.add(id);
      }
      return next;
    });
  }

  function handleCompare() {
    const ids = [...selected];
    if (ids.length === 2) {
      void navigate({ to: "/compare/$id1/$id2", params: { id1: ids[0], id2: ids[1] } });
    }
  }

  return (
    <div className="space-y-2">
      {completed.length >= 2 && (
        <div className="flex justify-end">
          <button
            onClick={handleCompare}
            disabled={selected.size !== 2}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground disabled:opacity-40"
          >
            <GitCompareArrows className="h-3.5 w-3.5" />
            Compare{selected.size > 0 ? ` (${selected.size}/2)` : ""}
          </button>
        </div>
      )}
      {investigations.map((inv) => {
        const config = STATUS_CONFIG[inv.status] ?? STATUS_CONFIG.pending!;
        const StatusIcon = config.icon;
        const isCompleted = inv.status === "completed";
        return (
          <div key={inv.id} className="flex items-center gap-2">
            {completed.length >= 2 && isCompleted && (
              <input
                type="checkbox"
                checked={selected.has(inv.id)}
                onChange={() => toggleSelect(inv.id)}
                className="h-3.5 w-3.5 shrink-0 rounded border-border accent-primary"
              />
            )}
            <Link
              to="/investigation/$id"
              params={{ id: inv.id }}
              className={cn(
                "flex flex-1 items-center justify-between rounded-lg border border-border bg-surface p-3",
                "transition-colors hover:border-primary/30",
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{inv.prompt}</p>
                <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                  {new Date(inv.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              <div className="ml-3 flex items-center gap-2">
                {inv.candidate_count > 0 && (
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {inv.candidate_count} candidates
                  </span>
                )}
                <span
                  className={cn(
                    "inline-flex items-center gap-1 text-xs",
                    config.className,
                  )}
                >
                  <StatusIcon className="h-3.5 w-3.5" />
                  {config.label}
                </span>
              </div>
            </Link>
          </div>
        );
      })}
    </div>
  );
}

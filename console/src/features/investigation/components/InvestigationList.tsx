import { Link } from "@tanstack/react-router";
import { Clock, FlaskConical, AlertCircle, CheckCircle2 } from "lucide-react";
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
  if (investigations.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">
        Recent Investigations
      </h2>
      <div className="space-y-2">
        {investigations.map((inv) => {
          const config = STATUS_CONFIG[inv.status] ?? STATUS_CONFIG.pending!;
          const StatusIcon = config.icon;
          return (
            <Link
              key={inv.id}
              to="/investigation/$id"
              params={{ id: inv.id }}
              className={cn(
                "flex items-center justify-between rounded-lg border border-border p-3",
                "transition-colors hover:bg-muted/50",
              )}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{inv.prompt}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
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
                  <span className="text-xs text-muted-foreground">
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
          );
        })}
      </div>
    </div>
  );
}

import { useState } from "react";
import { CheckCircle2, XCircle, Play } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { apiFetch } from "@/shared/lib/api";

interface PendingHypothesis {
  id: string;
  statement: string;
  rationale: string;
}

interface HypothesisApprovalCardProps {
  investigationId: string;
  hypotheses: PendingHypothesis[];
  onApproved: () => void;
}

export function HypothesisApprovalCard({
  investigationId,
  hypotheses,
  onApproved,
}: HypothesisApprovalCardProps) {
  const [rejected, setRejected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  function toggleReject(id: string) {
    setRejected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleApprove() {
    setSubmitting(true);
    const approvedIds = hypotheses.filter((h) => !rejected.has(h.id)).map((h) => h.id);
    const rejectedIds = hypotheses.filter((h) => rejected.has(h.id)).map((h) => h.id);
    await apiFetch(`/investigate/${investigationId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_ids: approvedIds, rejected_ids: rejectedIds }),
    });
    onApproved();
  }

  const approvedCount = hypotheses.length - rejected.size;

  return (
    <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-accent">
            Review Hypotheses Before Testing
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            The Director formulated {hypotheses.length} hypotheses. Approve or reject each before experiments begin.
          </p>
        </div>
        <button
          onClick={handleApprove}
          disabled={submitting || approvedCount === 0}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5" />
          {submitting ? "Starting..." : `Test ${approvedCount} Hypotheses`}
        </button>
      </div>
      <div className="mt-4 space-y-2">
        {hypotheses.map((h) => {
          const isRejected = rejected.has(h.id);
          return (
            <div
              key={h.id}
              className={cn(
                "flex items-start gap-3 rounded-lg border p-3 transition-colors",
                isRejected
                  ? "border-destructive/30 bg-destructive/5 opacity-60"
                  : "border-border bg-surface",
              )}
            >
              <button
                onClick={() => toggleReject(h.id)}
                className="mt-0.5 shrink-0"
              >
                {isRejected ? (
                  <XCircle className="h-5 w-5 text-destructive" />
                ) : (
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                )}
              </button>
              <div className="min-w-0">
                <p className={cn("text-sm", isRejected && "line-through")}>
                  {h.statement}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {h.rationale}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

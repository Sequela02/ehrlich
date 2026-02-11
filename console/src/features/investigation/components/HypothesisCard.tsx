import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/shared/lib/utils";
import type { Hypothesis } from "../types";

interface HypothesisCardProps {
  hypothesis: Hypothesis;
}

const STATUS_COLORS: Record<string, string> = {
  proposed: "border-muted-foreground/30 bg-muted/10",
  testing: "border-accent/40 bg-accent/5",
  supported: "border-secondary/40 bg-secondary/5",
  refuted: "border-destructive/40 bg-destructive/5",
  revised: "border-primary/40 bg-primary/5",
};

const STATUS_TEXT: Record<string, string> = {
  proposed: "text-muted-foreground",
  testing: "text-accent",
  supported: "text-secondary",
  refuted: "text-destructive",
  revised: "text-primary",
};

export function HypothesisCard({ hypothesis }: HypothesisCardProps) {
  const [expanded, setExpanded] = useState(false);

  const borderColor = STATUS_COLORS[hypothesis.status] ?? STATUS_COLORS.proposed;
  const textColor = STATUS_TEXT[hypothesis.status] ?? STATUS_TEXT.proposed;

  return (
    <div
      className={cn(
        "cursor-pointer rounded-lg border p-3 transition-colors hover:bg-muted/20",
        borderColor,
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-2">
        {expanded ? (
          <ChevronDown className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground/50" />
        ) : (
          <ChevronRight className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground/50" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={cn("text-xs font-medium", textColor)}>
              {hypothesis.status.toUpperCase()}
            </span>
            {hypothesis.confidence > 0 && (
              <span className="font-mono text-[10px] text-muted-foreground">
                {(hypothesis.confidence * 100).toFixed(0)}%
              </span>
            )}
            {hypothesis.parent_id && (
              <span className="rounded bg-muted px-1 font-mono text-[9px] text-muted-foreground">
                revised
              </span>
            )}
          </div>
          <p className="mt-1 text-xs leading-relaxed">{hypothesis.statement}</p>
          {expanded && (
            <div className="mt-2 space-y-1.5">
              <p className="text-[11px] italic text-muted-foreground">
                {hypothesis.rationale}
              </p>
              {hypothesis.supporting_evidence.length > 0 && (
                <div>
                  <span className="font-mono text-[10px] uppercase text-secondary/70">
                    Supporting ({hypothesis.supporting_evidence.length})
                  </span>
                  {hypothesis.supporting_evidence.map((e, i) => (
                    <div key={i} className="pl-2 text-[10px] text-secondary/60">
                      + {e}
                    </div>
                  ))}
                </div>
              )}
              {hypothesis.contradicting_evidence.length > 0 && (
                <div>
                  <span className="font-mono text-[10px] uppercase text-destructive/70">
                    Contradicting ({hypothesis.contradicting_evidence.length})
                  </span>
                  {hypothesis.contradicting_evidence.map((e, i) => (
                    <div key={i} className="pl-2 text-[10px] text-destructive/60">
                      - {e}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      {hypothesis.confidence > 0 && (
        <div className="mt-2 h-1 overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              hypothesis.status === "supported" && "bg-secondary",
              hypothesis.status === "refuted" && "bg-destructive",
              hypothesis.status === "testing" && "bg-accent",
              hypothesis.status === "revised" && "bg-primary",
              hypothesis.status === "proposed" && "bg-muted-foreground",
            )}
            style={{ width: `${hypothesis.confidence * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}

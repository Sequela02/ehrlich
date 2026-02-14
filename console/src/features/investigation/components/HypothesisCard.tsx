import { ChevronDown, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { Hypothesis } from "../types";
import { parseHypothesisStatement } from "../lib/parse-hypothesis";

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

  const parsed = useMemo(
    () => parseHypothesisStatement(hypothesis.statement),
    [hypothesis.statement],
  );

  const statusRow = (
    <div className="flex items-center gap-2">
      <span className={cn("text-xs font-medium", textColor)}>
        {hypothesis.status.toUpperCase()}
      </span>
      {hypothesis.prior_confidence > 0 && hypothesis.confidence === 0 && (
        <span className="font-mono text-[10px] text-muted-foreground">
          prior: {(hypothesis.prior_confidence * 100).toFixed(0)}%
        </span>
      )}
      {hypothesis.confidence > 0 && (
        <span className="font-mono text-[10px] text-muted-foreground">
          {hypothesis.prior_confidence > 0
            ? `${(hypothesis.prior_confidence * 100).toFixed(0)}% → ${(hypothesis.confidence * 100).toFixed(0)}%`
            : `${(hypothesis.confidence * 100).toFixed(0)}%`}
        </span>
      )}
      {hypothesis.parent_id && (
        <span className="rounded bg-muted px-1 font-mono text-[9px] text-muted-foreground">
          revised
        </span>
      )}
    </div>
  );

  const predictionChips = parsed.predictions.length > 0 ? (
    <div className="mt-1.5 flex flex-wrap gap-1">
      {parsed.predictions.map((p) => (
        <span
          key={p.label}
          className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
        >
          {p.label} {p.value}
        </span>
      ))}
    </div>
  ) : null;

  const expandedContent = expanded ? (
    <div className="mt-2 space-y-1.5">
      <p className="text-[11px] italic text-muted-foreground">
        {hypothesis.rationale}
      </p>
      {hypothesis.prediction && (
        <div className="rounded bg-primary/5 px-2 py-1.5">
          <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-primary/70">
            Prediction
          </span>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {hypothesis.prediction}
          </p>
        </div>
      )}
      {hypothesis.success_criteria && (
        <div className="flex gap-3 text-[10px]">
          <span className="text-secondary">Pass: {hypothesis.success_criteria}</span>
        </div>
      )}
      {hypothesis.failure_criteria && (
        <div className="flex gap-3 text-[10px]">
          <span className="text-destructive">Fail: {hypothesis.failure_criteria}</span>
        </div>
      )}
      {hypothesis.scope && (
        <p className="font-mono text-[10px] text-muted-foreground/60">
          Scope: {hypothesis.scope}
        </p>
      )}
      {parsed.smiles && (
        <div className="rounded bg-muted/30 px-2 py-1">
          <span className="select-all font-mono text-[10px] text-muted-foreground/70">
            {parsed.smiles}
          </span>
        </div>
      )}
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
  ) : null;

  return (
    <div
      className={cn(
        "cursor-pointer rounded-md border p-3 transition-colors hover:bg-muted/20",
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
          {statusRow}
          {parsed.smiles ? (
            <>
              <div className="mt-1.5 flex gap-3">
                <MolViewer2D
                  smiles={parsed.smiles}
                  width={80}
                  height={60}
                  className="shrink-0"
                />
                <div className="min-w-0">
                  {parsed.compoundName && (
                    <p className="text-xs font-medium text-foreground">
                      {parsed.compoundName}
                    </p>
                  )}
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                    {parsed.cleanedStatement}
                  </p>
                </div>
              </div>
              {predictionChips}
            </>
          ) : (
            <>
              <p className="mt-1 text-xs leading-relaxed">
                {hypothesis.statement}
              </p>
              {predictionChips}
            </>
          )}
          {expandedContent}
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

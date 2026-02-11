import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { CandidateRow } from "../types";
import { CandidateDetail } from "./CandidateDetail";

interface CandidateTableProps {
  candidates: CandidateRow[];
}

export function CandidateTable({ candidates }: CandidateTableProps) {
  const [expandedRank, setExpandedRank] = useState<number | null>(null);

  if (candidates.length === 0) {
    return null;
  }

  const hasScores = candidates.some(
    (c) =>
      (c.prediction_score && c.prediction_score > 0) ||
      (c.docking_score && c.docking_score !== 0) ||
      (c.admet_score && c.admet_score > 0) ||
      (c.resistance_risk && c.resistance_risk !== "unknown"),
  );

  return (
    <div className="space-y-3">
      <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Ranked Candidates
      </h3>
      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              <th className="w-8 px-2 py-2" />
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Rank
              </th>
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Structure
              </th>
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Name
              </th>
              {hasScores && (
                <>
                  <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    Pred.
                  </th>
                  <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    Dock.
                  </th>
                  <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    ADMET
                  </th>
                  <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    Resist.
                  </th>
                </>
              )}
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Notes
              </th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => {
              const isExpanded = expandedRank === c.rank;
              return (
                <CandidateRowComponent
                  key={c.rank}
                  candidate={c}
                  isExpanded={isExpanded}
                  hasScores={hasScores}
                  onToggle={() =>
                    setExpandedRank(isExpanded ? null : c.rank)
                  }
                />
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScoreCell({
  value,
  thresholds,
  format,
}: {
  value: number | undefined;
  thresholds: { good: number; ok: number; invert?: boolean };
  format: (v: number) => string;
}) {
  if (!value || value === 0) {
    return (
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground/30">
        --
      </td>
    );
  }
  const v = value;
  const { good, ok, invert } = thresholds;
  let color: string;
  if (invert) {
    color =
      v < good ? "text-primary" : v < ok ? "text-accent" : "text-muted-foreground";
  } else {
    color =
      v > good ? "text-primary" : v > ok ? "text-accent" : "text-muted-foreground";
  }
  return <td className={cn("px-3 py-2 font-mono text-xs", color)}>{format(v)}</td>;
}

function ResistanceCell({ risk }: { risk: string | undefined }) {
  if (!risk || risk === "unknown") {
    return (
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground/30">
        --
      </td>
    );
  }
  const color =
    risk === "low"
      ? "text-primary"
      : risk === "medium"
        ? "text-accent"
        : "text-destructive";
  return (
    <td className={cn("px-3 py-2 font-mono text-xs capitalize", color)}>
      {risk}
    </td>
  );
}

function CandidateRowComponent({
  candidate,
  isExpanded,
  hasScores,
  onToggle,
}: {
  candidate: CandidateRow;
  isExpanded: boolean;
  hasScores: boolean;
  onToggle: () => void;
}) {
  const Chevron = isExpanded ? ChevronDown : ChevronRight;
  const colSpan = hasScores ? 9 : 5;

  return (
    <>
      <tr
        className="cursor-pointer border-b border-border/30 last:border-0 hover:bg-muted/30"
        onClick={onToggle}
      >
        <td className="px-2 py-2">
          <Chevron className="h-4 w-4 text-muted-foreground" />
        </td>
        <td className="px-3 py-2 font-mono font-medium text-primary">
          {candidate.rank}
        </td>
        <td className="px-3 py-2">
          <MolViewer2D smiles={candidate.smiles} width={100} height={75} />
        </td>
        <td className="px-3 py-2">{candidate.name || "-"}</td>
        {hasScores && (
          <>
            <ScoreCell
              value={candidate.prediction_score}
              thresholds={{ good: 0.7, ok: 0.4 }}
              format={(v) => v.toFixed(2)}
            />
            <ScoreCell
              value={candidate.docking_score}
              thresholds={{ good: -7.0, ok: -5.0, invert: true }}
              format={(v) => v.toFixed(1)}
            />
            <ScoreCell
              value={candidate.admet_score}
              thresholds={{ good: 0.7, ok: 0.4 }}
              format={(v) => v.toFixed(2)}
            />
            <ResistanceCell risk={candidate.resistance_risk} />
          </>
        )}
        <td className="max-w-xs truncate px-3 py-2 text-xs text-muted-foreground">
          {candidate.notes || "-"}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={colSpan} className="border-b border-border/30 bg-muted/10">
            <CandidateDetail smiles={candidate.smiles} name={candidate.name} />
          </td>
        </tr>
      )}
    </>
  );
}

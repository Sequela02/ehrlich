import { useState } from "react";
import { ChevronDown, ChevronRight, GitCompareArrows } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { CandidateRow } from "../types";
import { CandidateDetail } from "./CandidateDetail";
import { CandidateComparison } from "./CandidateComparison";

interface CandidateTableProps {
  candidates: CandidateRow[];
}

export function CandidateTable({ candidates }: CandidateTableProps) {
  const [expandedRank, setExpandedRank] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [comparing, setComparing] = useState(false);

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

  function toggleSelect(rank: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(rank)) {
        next.delete(rank);
      } else if (next.size < 4) {
        next.add(rank);
      }
      return next;
    });
  }

  if (comparing && selected.size >= 2) {
    const compCandidates = candidates.filter((c) => selected.has(c.rank));
    return (
      <CandidateComparison
        candidates={compCandidates}
        onClose={() => setComparing(false)}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Ranked Candidates
          </h3>
          <p className="mt-1 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
            Top molecules identified by the investigation. Click a row to view 3D structure, properties, and drug-likeness profile.
          </p>
        </div>
        {candidates.length >= 2 && (
          <button
            onClick={() => setComparing(true)}
            disabled={selected.size < 2}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground disabled:opacity-40 disabled:hover:border-border disabled:hover:text-muted-foreground"
          >
            <GitCompareArrows className="h-3.5 w-3.5" />
            Compare{selected.size > 0 ? ` (${selected.size})` : ""}
          </button>
        )}
      </div>
      {hasScores && (
        <div className="rounded-md border border-border/50 bg-muted/30 px-3 py-2 text-[11px] text-muted-foreground">
          <span className="font-medium text-foreground/70">Score legend:</span>{" "}
          <span className="font-mono">Pred.</span> = ML activity prediction (0-1, higher is better) ·{" "}
          <span className="font-mono">Dock.</span> = binding affinity kcal/mol (more negative is better) ·{" "}
          <span className="font-mono">ADMET</span> = drug-likeness score (0-1, higher is better) ·{" "}
          <span className="font-mono">Resist.</span> = resistance risk (low/medium/high)
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              {candidates.length >= 2 && <th className="w-8 px-2 py-2" />}
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
                  isSelected={selected.has(c.rank)}
                  showSelect={candidates.length >= 2}
                  onToggle={() =>
                    setExpandedRank(isExpanded ? null : c.rank)
                  }
                  onSelect={() => toggleSelect(c.rank)}
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
  isSelected,
  showSelect,
  onToggle,
  onSelect,
}: {
  candidate: CandidateRow;
  isExpanded: boolean;
  hasScores: boolean;
  isSelected: boolean;
  showSelect: boolean;
  onToggle: () => void;
  onSelect: () => void;
}) {
  const Chevron = isExpanded ? ChevronDown : ChevronRight;
  const colSpan = (hasScores ? 9 : 5) + (showSelect ? 1 : 0);

  return (
    <>
      <tr
        className="cursor-pointer border-b border-border/30 last:border-0 hover:bg-muted/30"
        onClick={onToggle}
      >
        {showSelect && (
          <td className="px-2 py-2">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                onSelect();
              }}
              onClick={(e) => e.stopPropagation()}
              className="h-3.5 w-3.5 rounded border-border accent-primary"
            />
          </td>
        )}
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
        <td className="min-w-[200px] max-w-lg px-3 py-2 text-xs leading-relaxed text-muted-foreground">
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

import { X } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { CandidateRow } from "../types";

interface CandidateComparisonProps {
  candidates: CandidateRow[];
  onClose: () => void;
}

const SCORE_ROWS: {
  label: string;
  key: keyof CandidateRow;
  format: (v: unknown) => string;
  isBest: (a: number, b: number) => boolean;
}[] = [
  {
    label: "Prediction",
    key: "prediction_score",
    format: (v) => (v != null && v !== 0 ? (v as number).toFixed(2) : "-"),
    isBest: (a, b) => a > b,
  },
  {
    label: "Docking",
    key: "docking_score",
    format: (v) => (v != null && v !== 0 ? `${(v as number).toFixed(1)}` : "-"),
    isBest: (a, b) => a < b,
  },
  {
    label: "ADMET",
    key: "admet_score",
    format: (v) => (v != null && v !== 0 ? (v as number).toFixed(2) : "-"),
    isBest: (a, b) => a > b,
  },
  {
    label: "Resistance",
    key: "resistance_risk",
    format: (v) => (v as string) || "-",
    isBest: () => false,
  },
];

function bestIndex(candidates: CandidateRow[], key: keyof CandidateRow, isBest: (a: number, b: number) => boolean): number {
  let best = -1;
  let bestVal = 0;
  for (let i = 0; i < candidates.length; i++) {
    const v = candidates[i][key] as number;
    if (v == null || v === 0) continue;
    if (best === -1 || isBest(v, bestVal)) {
      best = i;
      bestVal = v;
    }
  }
  return best;
}

export function CandidateComparison({ candidates, onClose }: CandidateComparisonProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Comparing {candidates.length} Candidates
        </h3>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-4 py-2 text-left font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Property
              </th>
              {candidates.map((c) => (
                <th
                  key={c.rank}
                  className="px-4 py-2 text-center font-mono text-[11px] font-medium uppercase tracking-wider text-primary"
                >
                  #{c.rank} {c.name || ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Structure row */}
            <tr className="border-b border-border/30">
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground">Structure</td>
              {candidates.map((c) => (
                <td key={c.rank} className="px-4 py-3 text-center">
                  <div className="inline-block">
                    <MolViewer2D smiles={c.smiles} width={120} height={90} />
                  </div>
                </td>
              ))}
            </tr>
            {/* SMILES row */}
            <tr className="border-b border-border/30">
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">SMILES</td>
              {candidates.map((c) => (
                <td key={c.rank} className="max-w-[200px] break-all px-4 py-2 font-mono text-[10px] text-muted-foreground">
                  {c.smiles}
                </td>
              ))}
            </tr>
            {/* Score rows */}
            {SCORE_ROWS.map((row) => {
              const best = row.key !== "resistance_risk" ? bestIndex(candidates, row.key, row.isBest) : -1;
              return (
                <tr key={row.label} className="border-b border-border/30 last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                    {row.label}
                  </td>
                  {candidates.map((c, i) => (
                    <td
                      key={c.rank}
                      className={cn(
                        "px-4 py-2 text-center font-mono text-xs",
                        i === best ? "font-medium text-primary" : "text-muted-foreground",
                      )}
                    >
                      {row.format(c[row.key])}
                    </td>
                  ))}
                </tr>
              );
            })}
            {/* Notes row */}
            <tr>
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">Notes</td>
              {candidates.map((c) => (
                <td key={c.rank} className="px-4 py-2 text-xs leading-relaxed text-muted-foreground">
                  {c.notes || "-"}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

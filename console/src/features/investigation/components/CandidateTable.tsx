import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

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
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Rank</th>
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Structure</th>
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Name</th>
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Notes</th>
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
                  onToggle={() => setExpandedRank(isExpanded ? null : c.rank)}
                />
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CandidateRowComponent({
  candidate,
  isExpanded,
  onToggle,
}: {
  candidate: CandidateRow;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const Chevron = isExpanded ? ChevronDown : ChevronRight;

  return (
    <>
      <tr
        className="cursor-pointer border-b border-border/30 last:border-0 hover:bg-muted/30"
        onClick={onToggle}
      >
        <td className="px-2 py-2">
          <Chevron className="h-4 w-4 text-muted-foreground" />
        </td>
        <td className="px-3 py-2 font-mono font-medium text-primary">{candidate.rank}</td>
        <td className="px-3 py-2">
          <MolViewer2D smiles={candidate.smiles} width={80} height={60} />
        </td>
        <td className="px-3 py-2">{candidate.name || "-"}</td>
        <td className="max-w-xs truncate px-3 py-2 text-xs text-muted-foreground">
          {candidate.notes || "-"}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={5} className="border-b border-border/30 bg-muted/10">
            <CandidateDetail smiles={candidate.smiles} name={candidate.name} />
          </td>
        </tr>
      )}
    </>
  );
}

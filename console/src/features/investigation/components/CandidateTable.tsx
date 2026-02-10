import type { CandidateRow } from "../types";

interface CandidateTableProps {
  candidates: CandidateRow[];
}

export function CandidateTable({ candidates }: CandidateTableProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Ranked Candidates</h3>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Rank</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Name</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">SMILES</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Notes</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.rank} className="border-b border-border/50 last:border-0">
                <td className="px-3 py-2 font-medium">{c.rank}</td>
                <td className="px-3 py-2">{c.name || "-"}</td>
                <td className="px-3 py-2 font-mono text-xs">{c.smiles}</td>
                <td className="max-w-xs truncate px-3 py-2 text-xs text-muted-foreground">
                  {c.notes || "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import type { CandidateRow } from "../types";

interface CandidateTableProps {
  candidates: CandidateRow[];
}

export function CandidateTable({ candidates }: CandidateTableProps) {
  if (candidates.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No candidates yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="pb-2 font-medium">Rank</th>
            <th className="pb-2 font-medium">Name</th>
            <th className="pb-2 font-medium">SMILES</th>
            <th className="pb-2 font-medium">Prediction</th>
            <th className="pb-2 font-medium">Docking</th>
            <th className="pb-2 font-medium">ADMET</th>
            <th className="pb-2 font-medium">Resistance</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr key={c.rank} className="border-b border-border/50">
              <td className="py-2">{c.rank}</td>
              <td className="py-2">{c.name || "-"}</td>
              <td className="py-2 font-mono text-xs">{c.smiles}</td>
              <td className="py-2">{c.predictionScore.toFixed(3)}</td>
              <td className="py-2">{c.dockingScore.toFixed(2)}</td>
              <td className="py-2">{c.admetScore.toFixed(2)}</td>
              <td className="py-2">{c.resistanceRisk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

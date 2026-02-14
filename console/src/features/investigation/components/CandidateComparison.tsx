import { X } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { CandidateRow, DomainDisplayConfig } from "../types";

interface CandidateComparisonProps {
  candidates: CandidateRow[];
  domainConfig?: DomainDisplayConfig | null;
  onClose: () => void;
}

export function CandidateComparison({ candidates, domainConfig, onClose }: CandidateComparisonProps) {
  const scoreColumns = domainConfig?.score_columns ?? [];
  const attributeKeys = domainConfig?.attribute_keys ?? [];
  const isMolecular = !domainConfig || domainConfig.identifier_type === "smiles";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
          Comparing {candidates.length} Candidates
        </h3>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
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
            {/* Structure row (molecular only) */}
            {isMolecular && (
              <tr className="border-b border-border/30">
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">Structure</td>
                {candidates.map((c) => (
                  <td key={c.rank} className="px-4 py-3 text-center">
                    <div className="inline-block">
                      <MolViewer2D smiles={c.identifier} width={120} height={90} />
                    </div>
                  </td>
                ))}
              </tr>
            )}
            {/* Identifier row */}
            <tr className="border-b border-border/30">
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                {domainConfig?.identifier_label ?? "Identifier"}
              </td>
              {candidates.map((c) => (
                <td key={c.rank} className="max-w-[200px] break-all px-4 py-2 font-mono text-[10px] text-muted-foreground">
                  {c.identifier}
                </td>
              ))}
            </tr>
            {/* Dynamic score rows */}
            {scoreColumns.map((col) => {
              const best = findBestIndex(candidates, col.key, col.higher_is_better);
              return (
                <tr key={col.key} className="border-b border-border/30 last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                    {col.label}
                  </td>
                  {candidates.map((c, i) => {
                    const v = c.scores[col.key];
                    const decimals = col.format_spec.includes("f") ? parseInt(col.format_spec.replace(/[^0-9]/g, "")) || 2 : 2;
                    return (
                      <td
                        key={c.rank}
                        className={cn(
                          "px-4 py-2 text-center font-mono text-xs",
                          i === best ? "font-medium text-primary" : "text-muted-foreground",
                        )}
                      >
                        {v != null && v !== 0 ? v.toFixed(decimals) : "-"}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
            {/* Attribute rows */}
            {attributeKeys.map((key) => (
              <tr key={key} className="border-b border-border/30 last:border-0">
                <td className="px-4 py-2 font-mono text-xs capitalize text-muted-foreground">
                  {key.replace(/_/g, " ")}
                </td>
                {candidates.map((c) => (
                  <td
                    key={c.rank}
                    className="px-4 py-2 text-center font-mono text-xs text-muted-foreground"
                  >
                    {c.attributes[key] || "-"}
                  </td>
                ))}
              </tr>
            ))}
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

function findBestIndex(
  candidates: CandidateRow[],
  scoreKey: string,
  higherIsBetter: boolean,
): number {
  let best = -1;
  let bestVal = 0;
  for (let i = 0; i < candidates.length; i++) {
    const v = candidates[i].scores[scoreKey];
    if (v == null || v === 0) continue;
    if (best === -1 || (higherIsBetter ? v > bestVal : v < bestVal)) {
      best = i;
      bestVal = v;
    }
  }
  return best;
}

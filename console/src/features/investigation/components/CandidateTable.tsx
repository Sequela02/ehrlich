import { useState } from "react";
import { ChevronDown, ChevronRight, GitCompareArrows, Square, CheckSquare } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule";
import type { CandidateRow, DomainDisplayConfig } from "../types";
import { CandidateDetail } from "./CandidateDetail";
import { CandidateComparison } from "./CandidateComparison";

interface CandidateTableProps {
  candidates: CandidateRow[];
  domainConfig?: DomainDisplayConfig | null;
}

export function CandidateTable({ candidates, domainConfig }: CandidateTableProps) {
  const [expandedRank, setExpandedRank] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [comparing, setComparing] = useState(false);

  if (candidates.length === 0) {
    return null;
  }

  const scoreColumns = domainConfig?.score_columns ?? [];
  const attributeKeys = domainConfig?.attribute_keys ?? [];
  const candidateLabel = domainConfig?.candidate_label ?? "Ranked Candidates";
  const isMolecular = !domainConfig || domainConfig.identifier_type === "smiles";

  const hasScores = candidates.some(
    (c) => Object.keys(c.scores).length > 0 || Object.keys(c.attributes).length > 0,
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
        domainConfig={domainConfig}
        onClose={() => setComparing(false)}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
            {candidateLabel}
          </h3>
          <p className="mt-1 pl-4 text-xs leading-relaxed text-muted-foreground/50">
            {isMolecular
              ? "Top molecules identified by the investigation. Click a row to view 3D structure, properties, and drug-likeness profile."
              : "Top candidates identified by the investigation. Click a row to view details."}
          </p>
        </div>
        {candidates.length >= 2 && (
          <button
            onClick={() => setComparing(true)}
            disabled={selected.size < 2}
            className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground disabled:opacity-40 disabled:hover:border-border disabled:hover:text-muted-foreground"
          >
            <GitCompareArrows className="h-3.5 w-3.5" />
            Compare{selected.size > 0 ? ` (${selected.size})` : ""}
          </button>
        )}
      </div>
      {hasScores && scoreColumns.length > 0 && (
        <div className="rounded-md border border-border/50 bg-muted/30 px-3 py-2 text-[11px] text-muted-foreground">
          <span className="font-medium text-foreground/70">Score legend:</span>{" "}
          {scoreColumns.map((col, i) => (
            <span key={col.key}>
              <span className="font-mono">{col.label}</span> = {col.higher_is_better ? "higher is better" : "lower is better"}
              {i < scoreColumns.length - 1 ? " · " : ""}
            </span>
          ))}
        </div>
      )}
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              {candidates.length >= 2 && <th className="w-8 px-2 py-2" />}
              <th className="w-8 px-2 py-2" />
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Rank
              </th>
              {isMolecular && (
                <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Structure
                </th>
              )}
              <th className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Name
              </th>
              {hasScores && scoreColumns.map((col) => (
                <th key={col.key} className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  {col.label}
                </th>
              ))}
              {hasScores && attributeKeys.map((key) => (
                <th key={key} className="px-3 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground capitalize">
                  {key.replace(/_/g, " ")}
                </th>
              ))}
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
                  scoreColumns={scoreColumns}
                  attributeKeys={attributeKeys}
                  isMolecular={isMolecular}
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

function DynamicScoreCell({
  value,
  good,
  ok,
  higherIsBetter,
  formatSpec,
}: {
  value: number | undefined;
  good: number;
  ok: number;
  higherIsBetter: boolean;
  formatSpec: string;
}) {
  if (value == null || value === 0) {
    return (
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground/30">
        --
      </td>
    );
  }
  let color: string;
  if (higherIsBetter) {
    color = value > good ? "text-primary" : value > ok ? "text-accent" : "text-muted-foreground";
  } else {
    color = value < good ? "text-primary" : value < ok ? "text-accent" : "text-muted-foreground";
  }
  const decimals = formatSpec.includes("f") ? parseInt(formatSpec.replace(/[^0-9]/g, "")) || 2 : 2;
  return <td className={cn("px-3 py-2 font-mono text-xs", color)}>{value.toFixed(decimals)}</td>;
}

function AttributeCell({ value }: { value: string | undefined }) {
  if (!value || value === "unknown") {
    return (
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground/30">
        --
      </td>
    );
  }
  const color =
    value === "low"
      ? "text-primary"
      : value === "medium"
        ? "text-accent"
        : value === "high"
          ? "text-destructive"
          : "text-muted-foreground";
  return (
    <td className={cn("px-3 py-2 font-mono text-xs capitalize", color)}>
      {value}
    </td>
  );
}

function CandidateRowComponent({
  candidate,
  isExpanded,
  hasScores,
  scoreColumns,
  attributeKeys,
  isMolecular,
  isSelected,
  showSelect,
  onToggle,
  onSelect,
}: {
  candidate: CandidateRow;
  isExpanded: boolean;
  hasScores: boolean;
  scoreColumns: { key: string; good_threshold: number; ok_threshold: number; higher_is_better: boolean; format_spec: string }[];
  attributeKeys: string[];
  isMolecular: boolean;
  isSelected: boolean;
  showSelect: boolean;
  onToggle: () => void;
  onSelect: () => void;
}) {
  const Chevron = isExpanded ? ChevronDown : ChevronRight;
  const baseCols = 3 + (isMolecular ? 1 : 0) + (showSelect ? 1 : 0);
  const scoreCols = hasScores ? scoreColumns.length + attributeKeys.length : 0;
  const colSpan = baseCols + scoreCols + 1; // +1 for notes

  return (
    <>
      <tr
        className="cursor-pointer border-b border-border/30 last:border-0 hover:bg-muted/30"
        onClick={onToggle}
      >
        {showSelect && (
          <td className="px-2 py-2">
            <button
              onClick={(e) => { e.stopPropagation(); onSelect(); }}
              className="text-muted-foreground transition-colors hover:text-primary"
            >
              {isSelected
                ? <CheckSquare className="h-4 w-4 text-primary" />
                : <Square className="h-4 w-4" />}
            </button>
          </td>
        )}
        <td className="px-2 py-2">
          <Chevron className="h-4 w-4 text-muted-foreground" />
        </td>
        <td className="px-3 py-2 font-mono font-medium text-primary">
          {candidate.rank}
        </td>
        {isMolecular && (
          <td className="px-3 py-2">
            <MolViewer2D smiles={candidate.identifier} width={100} height={75} />
          </td>
        )}
        <td className="px-3 py-2">{candidate.name || "-"}</td>
        {hasScores && scoreColumns.map((col) => (
          <DynamicScoreCell
            key={col.key}
            value={candidate.scores[col.key]}
            good={col.good_threshold}
            ok={col.ok_threshold}
            higherIsBetter={col.higher_is_better}
            formatSpec={col.format_spec}
          />
        ))}
        {hasScores && attributeKeys.map((key) => (
          <AttributeCell key={key} value={candidate.attributes[key]} />
        ))}
        <td className="min-w-[200px] max-w-lg px-3 py-2 text-xs leading-relaxed text-muted-foreground">
          {candidate.notes || "-"}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={colSpan} className="border-b border-border/30 bg-muted/10">
            <CandidateDetail
              identifier={candidate.identifier}
              identifierType={candidate.identifier_type}
              name={candidate.name}
              scores={candidate.scores}
              attributes={candidate.attributes}
            />
          </td>
        </tr>
      )}
    </>
  );
}

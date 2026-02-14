import { useMemo } from "react";
import Markdown from "react-markdown";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule";
import { VIZ_COLORS } from "@/features/visualization/theme";
import type { InvestigationDetail, CandidateRow, Finding } from "../types";

interface InvestigationComparisonProps {
  invA: InvestigationDetail;
  invB: InvestigationDetail;
}

function findShared(a: CandidateRow[], b: CandidateRow[]): string[] {
  const idsB = new Set(b.map((c) => c.identifier));
  return a.filter((c) => idsB.has(c.identifier)).map((c) => c.identifier);
}

// ── Finding overlap detection ────────────────────────────────────────

function wordSet(text: string): Set<string> {
  return new Set(text.toLowerCase().split(/\s+/).filter(Boolean));
}

function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 1;
  let intersection = 0;
  for (const w of a) {
    if (b.has(w)) intersection++;
  }
  const union = a.size + b.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

interface FindingDiff {
  uniqueA: Finding[];
  shared: { a: Finding; b: Finding }[];
  uniqueB: Finding[];
}

function diffFindings(aFindings: Finding[], bFindings: Finding[]): FindingDiff {
  const matchedB = new Set<number>();
  const shared: { a: Finding; b: Finding }[] = [];
  const uniqueA: Finding[] = [];

  for (const fa of aFindings) {
    let matched = false;
    for (let j = 0; j < bFindings.length; j++) {
      if (matchedB.has(j)) continue;
      const fb = bFindings[j];
      // Match by provenance if both have source_type + source_id
      if (fa.source_type && fa.source_id && fb.source_type && fb.source_id) {
        if (fa.source_type === fb.source_type && fa.source_id === fb.source_id) {
          shared.push({ a: fa, b: fb });
          matchedB.add(j);
          matched = true;
          break;
        }
      }
      // Fallback: title similarity
      if (jaccard(wordSet(fa.title), wordSet(fb.title)) > 0.8) {
        shared.push({ a: fa, b: fb });
        matchedB.add(j);
        matched = true;
        break;
      }
    }
    if (!matched) uniqueA.push(fa);
  }

  const uniqueB = bFindings.filter((_, i) => !matchedB.has(i));
  return { uniqueA, shared, uniqueB };
}

// ── Score chart data ─────────────────────────────────────────────────

function buildScoreChartData(
  sharedIds: string[],
  candidatesA: CandidateRow[],
  candidatesB: CandidateRow[],
): { data: Record<string, string | number>[]; keys: string[] } | null {
  const mapA = new Map(candidatesA.map((c) => [c.identifier, c]));
  const mapB = new Map(candidatesB.map((c) => [c.identifier, c]));
  const allKeys = new Set<string>();
  const data: Record<string, string | number>[] = [];

  for (const id of sharedIds) {
    const a = mapA.get(id);
    const b = mapB.get(id);
    if (!a || !b) continue;
    const entry: Record<string, string | number> = {
      name: a.name || id.slice(0, 20),
    };
    for (const [k, v] of Object.entries(a.scores)) {
      if (typeof v === "number") {
        entry[`${k}_A`] = Number(v.toFixed(3));
        allKeys.add(k);
      }
    }
    for (const [k, v] of Object.entries(b.scores)) {
      if (typeof v === "number") {
        entry[`${k}_B`] = Number(v.toFixed(3));
        allKeys.add(k);
      }
    }
    data.push(entry);
  }

  if (data.length === 0 || allKeys.size === 0) return null;
  return { data, keys: [...allKeys] };
}

// ── Cost parsing ─────────────────────────────────────────────────────

interface ParsedCost {
  inputTokens: number;
  outputTokens: number;
  toolCalls: number;
  totalCost: number;
}

function parseCostData(cost_data: Record<string, unknown>): ParsedCost | null {
  const input = cost_data.input_tokens ?? cost_data.inputTokens;
  const output = cost_data.output_tokens ?? cost_data.outputTokens;
  const tools = cost_data.tool_calls ?? cost_data.toolCalls;
  const total = cost_data.total_cost_usd ?? cost_data.totalCost;
  if (input == null && output == null) return null;
  return {
    inputTokens: Number(input ?? 0),
    outputTokens: Number(output ?? 0),
    toolCalls: Number(tools ?? 0),
    totalCost: Number(total ?? 0),
  };
}

// ── Main component ───────────────────────────────────────────────────

export function InvestigationComparison({ invA, invB }: InvestigationComparisonProps) {
  const sharedIdentifiers = findShared(invA.candidates, invB.candidates);
  const findingDiff = useMemo(() => diffFindings(invA.findings, invB.findings), [invA.findings, invB.findings]);
  const scoreChart = useMemo(
    () => buildScoreChartData(sharedIdentifiers, invA.candidates, invB.candidates),
    [sharedIdentifiers, invA.candidates, invB.candidates],
  );
  const costA = parseCostData(invA.cost_data);
  const costB = parseCostData(invB.cost_data);

  const supportingA = invA.findings.filter((f) => f.evidence_type === "supporting").length;
  const supportingB = invB.findings.filter((f) => f.evidence_type === "supporting").length;

  return (
    <div className="space-y-6">
      {/* Enhanced stats bar */}
      <div className="grid grid-cols-5 gap-4">
        <StatCard label="A Candidates" value={String(invA.candidates.length)} />
        <StatCard
          label="A Findings"
          value={`${invA.findings.length} (${invA.findings.length > 0 ? Math.round((supportingA / invA.findings.length) * 100) : 0}% sup.)`}
        />
        <StatCard label="Shared Candidates" value={`${sharedIdentifiers.length} overlap`} accent />
        <StatCard
          label="B Findings"
          value={`${invB.findings.length} (${invB.findings.length > 0 ? Math.round((supportingB / invB.findings.length) * 100) : 0}% sup.)`}
        />
        <StatCard label="B Candidates" value={String(invB.candidates.length)} />
      </div>

      {/* Side-by-side prompts */}
      <div className="grid grid-cols-2 gap-4">
        <PromptCard prompt={invA.prompt} status={invA.status} />
        <PromptCard prompt={invB.prompt} status={invB.status} />
      </div>

      {/* Summary comparison */}
      {(invA.summary || invB.summary) && (
        <div className="grid grid-cols-2 gap-4">
          <SummaryCard summary={invA.summary} label="Investigation A" />
          <SummaryCard summary={invB.summary} label="Investigation B" />
        </div>
      )}

      {/* Side-by-side candidates */}
      <div className="grid grid-cols-2 gap-4">
        <CandidateList title="Investigation A" candidates={invA.candidates} sharedIdentifiers={sharedIdentifiers} />
        <CandidateList title="Investigation B" candidates={invB.candidates} sharedIdentifiers={sharedIdentifiers} />
      </div>

      {/* Shared candidates detail */}
      {sharedIdentifiers.length > 0 && (
        <div className="space-y-3">
          <h3 className="border-l-2 border-accent pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
            Shared Candidates ({sharedIdentifiers.length})
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sharedIdentifiers.map((id) => {
              const fromA = invA.candidates.find((c) => c.identifier === id);
              const fromB = invB.candidates.find((c) => c.identifier === id);
              const isMolecular = fromA?.identifier_type === "smiles";
              return (
                <div key={id} className="rounded-md border border-accent/30 bg-accent/5 p-3">
                  {isMolecular && (
                    <div className="flex justify-center">
                      <MolViewer2D smiles={id} width={120} height={90} />
                    </div>
                  )}
                  <p className="mt-2 text-center text-xs font-medium">
                    {fromA?.name || fromB?.name || "unnamed"}
                  </p>
                  <div className="mt-2 grid grid-cols-2 gap-2 font-mono text-[10px]">
                    <div>
                      <span className="text-muted-foreground">A rank:</span>{" "}
                      <span className="text-primary">{fromA?.rank ?? "-"}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">B rank:</span>{" "}
                      <span className="text-primary">{fromB?.rank ?? "-"}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Score comparison chart */}
      {scoreChart && (
        <div className="space-y-3">
          <h3 className="border-l-2 border-accent pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
            Score Comparison
          </h3>
          <div className="rounded-md border border-border bg-surface p-4">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreChart.data}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: VIZ_COLORS.text }} />
                <YAxis tick={{ fontSize: 10, fill: VIZ_COLORS.text }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: VIZ_COLORS.surface,
                    border: `1px solid ${VIZ_COLORS.grid}`,
                    fontSize: 11,
                    color: VIZ_COLORS.text,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                {scoreChart.keys.map((key) => (
                  <Bar key={`${key}_A`} dataKey={`${key}_A`} name={`${key} (A)`} fill={VIZ_COLORS.primary} />
                ))}
                {scoreChart.keys.map((key) => (
                  <Bar key={`${key}_B`} dataKey={`${key}_B`} name={`${key} (B)`} fill={VIZ_COLORS.warning} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Findings comparison */}
      {(invA.findings.length > 0 || invB.findings.length > 0) && (
        <div className="space-y-3">
          <h3 className="border-l-2 border-accent pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
            Findings Comparison
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <FindingColumn label="Only in A" findings={findingDiff.uniqueA} />
            <FindingColumn
              label={`Shared (${findingDiff.shared.length})`}
              findings={findingDiff.shared.map((s) => s.a)}
              accent
            />
            <FindingColumn label="Only in B" findings={findingDiff.uniqueB} />
          </div>
        </div>
      )}

      {/* Cost comparison */}
      {(costA || costB) && (
        <div className="space-y-3">
          <h3 className="border-l-2 border-accent pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
            Cost Comparison
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <CostCard cost={costA} label="Investigation A" />
            <CostCard cost={costB} label="Investigation B" />
          </div>
        </div>
      )}

      {/* Hypothesis summary */}
      <div className="grid grid-cols-2 gap-4">
        <HypothesisSummary title="Investigation A" hypotheses={invA.hypotheses} />
        <HypothesisSummary title="Investigation B" hypotheses={invB.hypotheses} />
      </div>
    </div>
  );
}

// ── Inline helper components ─────────────────────────────────────────

function StatCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={cn("rounded-md border p-3 text-center", accent ? "border-accent/30 bg-accent/5" : "border-border bg-surface")}>
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-sm font-medium", accent ? "text-accent" : "text-foreground")}>{value}</p>
    </div>
  );
}

function PromptCard({ prompt, status }: { prompt: string; status: string }) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <span className={cn(
        "font-mono text-[10px] uppercase",
        status === "completed" ? "text-secondary" : "text-muted-foreground",
      )}>
        {status}
      </span>
      <p className="mt-1 text-sm leading-relaxed">{prompt}</p>
    </div>
  );
}

function SummaryCard({ summary, label }: { summary: string; label: string }) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</h4>
      <div className="prose prose-invert prose-sm max-w-none text-xs leading-relaxed text-muted-foreground">
        <Markdown>{summary || "No summary available."}</Markdown>
      </div>
    </div>
  );
}

function CandidateList({
  title,
  candidates,
  sharedIdentifiers,
}: {
  title: string;
  candidates: CandidateRow[];
  sharedIdentifiers: string[];
}) {
  const sharedSet = new Set(sharedIdentifiers);
  return (
    <div className="space-y-2">
      <h4 className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</h4>
      <div className="space-y-1.5">
        {candidates.slice(0, 10).map((c) => {
          const topScore = Object.values(c.scores)[0];
          return (
            <div
              key={c.rank}
              className={cn(
                "flex items-center gap-2 rounded-md border p-2 text-xs",
                sharedSet.has(c.identifier) ? "border-accent/30 bg-accent/5" : "border-border bg-surface",
              )}
            >
              <span className="font-mono font-medium text-primary">#{c.rank}</span>
              <span className="truncate">{c.name || c.identifier.slice(0, 30)}</span>
              {topScore != null && topScore > 0 && (
                <span className="ml-auto font-mono text-muted-foreground">{topScore.toFixed(2)}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FindingColumn({
  label,
  findings,
  accent,
}: {
  label: string;
  findings: Finding[];
  accent?: boolean;
}) {
  const EVIDENCE_BADGE: Record<string, string> = {
    supporting: "text-secondary",
    contradicting: "text-destructive",
    neutral: "text-muted-foreground",
  };

  return (
    <div className="space-y-2">
      <h4 className={cn("font-mono text-[10px] uppercase tracking-wider", accent ? "text-accent" : "text-muted-foreground")}>
        {label}
      </h4>
      <div className="space-y-1.5">
        {findings.length === 0 && (
          <p className="text-xs italic text-muted-foreground">None</p>
        )}
        {findings.map((f, i) => (
          <div
            key={i}
            className={cn(
              "rounded-md border p-2 text-xs",
              accent ? "border-accent/30 bg-accent/5" : "border-border bg-surface",
            )}
          >
            <p className="font-medium leading-snug">{f.title}</p>
            <div className="mt-1 flex items-center gap-2">
              <span className={cn("font-mono text-[10px]", EVIDENCE_BADGE[f.evidence_type] ?? "text-muted-foreground")}>
                {f.evidence_type}
              </span>
              {f.source_type && (
                <span className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground">
                  {f.source_type}{f.source_id ? `: ${f.source_id}` : ""}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CostCard({ cost, label }: { cost: ParsedCost | null; label: string }) {
  if (!cost) {
    return (
      <div className="rounded-md border border-border bg-surface p-4">
        <h4 className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</h4>
        <p className="mt-2 text-xs italic text-muted-foreground">No cost data</p>
      </div>
    );
  }
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h4 className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</h4>
      <div className="grid grid-cols-2 gap-2 font-mono text-xs">
        <div>
          <span className="text-muted-foreground">Input: </span>
          <span>{cost.inputTokens.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Output: </span>
          <span>{cost.outputTokens.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Tool calls: </span>
          <span>{cost.toolCalls.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Total: </span>
          <span className="text-primary">${cost.totalCost.toFixed(4)}</span>
        </div>
      </div>
    </div>
  );
}

function HypothesisSummary({
  title,
  hypotheses,
}: {
  title: string;
  hypotheses: { status: string; statement: string }[];
}) {
  const counts = hypotheses.reduce<Record<string, number>>((acc, h) => {
    acc[h.status] = (acc[h.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="rounded-md border border-border bg-surface p-3">
      <h4 className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</h4>
      <div className="mt-2 flex gap-3 font-mono text-[10px]">
        {Object.entries(counts).map(([status, count]) => (
          <span key={status} className={cn(
            status === "supported" ? "text-secondary" :
              status === "refuted" ? "text-destructive" :
                status === "revised" ? "text-primary" : "text-muted-foreground",
          )}>
            {count} {status}
          </span>
        ))}
      </div>
    </div>
  );
}

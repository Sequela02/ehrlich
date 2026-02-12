import { cn } from "@/shared/lib/utils";
import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import type { InvestigationDetail, CandidateRow } from "../types";

interface InvestigationComparisonProps {
  invA: InvestigationDetail;
  invB: InvestigationDetail;
}

function findShared(a: CandidateRow[], b: CandidateRow[]): string[] {
  const idsB = new Set(b.map((c) => c.identifier));
  return a.filter((c) => idsB.has(c.identifier)).map((c) => c.identifier);
}

export function InvestigationComparison({ invA, invB }: InvestigationComparisonProps) {
  const sharedIdentifiers = findShared(invA.candidates, invB.candidates);

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Investigation A" value={`${invA.candidates.length} candidates`} />
        <StatCard label="Shared Candidates" value={`${sharedIdentifiers.length} overlap`} accent />
        <StatCard label="Investigation B" value={`${invB.candidates.length} candidates`} />
      </div>

      {/* Side-by-side prompts */}
      <div className="grid grid-cols-2 gap-4">
        <PromptCard prompt={invA.prompt} status={invA.status} />
        <PromptCard prompt={invB.prompt} status={invB.status} />
      </div>

      {/* Side-by-side candidates */}
      <div className="grid grid-cols-2 gap-4">
        <CandidateList title="Investigation A" candidates={invA.candidates} sharedIdentifiers={sharedIdentifiers} />
        <CandidateList title="Investigation B" candidates={invB.candidates} sharedIdentifiers={sharedIdentifiers} />
      </div>

      {/* Shared candidates detail */}
      {sharedIdentifiers.length > 0 && (
        <div className="space-y-3">
          <h3 className="border-l-2 border-accent pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Shared Candidates ({sharedIdentifiers.length})
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sharedIdentifiers.map((id) => {
              const fromA = invA.candidates.find((c) => c.identifier === id);
              const fromB = invB.candidates.find((c) => c.identifier === id);
              const isMolecular = fromA?.identifier_type === "smiles";
              return (
                <div key={id} className="rounded-lg border border-accent/30 bg-accent/5 p-3">
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

      {/* Hypothesis summary */}
      <div className="grid grid-cols-2 gap-4">
        <HypothesisSummary title="Investigation A" hypotheses={invA.hypotheses} />
        <HypothesisSummary title="Investigation B" hypotheses={invB.hypotheses} />
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={cn("rounded-lg border p-3 text-center", accent ? "border-accent/30 bg-accent/5" : "border-border bg-surface")}>
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-sm font-medium", accent ? "text-accent" : "text-foreground")}>{value}</p>
    </div>
  );
}

function PromptCard({ prompt, status }: { prompt: string; status: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
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
    <div className="rounded-lg border border-border bg-surface p-3">
      <h4 className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</h4>
      <div className="mt-2 flex gap-3 font-mono text-[10px]">
        {Object.entries(counts).map(([status, count]) => (
          <span key={status} className={cn(
            status === "supported" ? "text-secondary" :
            status === "refuted" ? "text-destructive" :
            status === "revised" ? "text-amber-400" : "text-muted-foreground",
          )}>
            {count} {status}
          </span>
        ))}
      </div>
    </div>
  );
}

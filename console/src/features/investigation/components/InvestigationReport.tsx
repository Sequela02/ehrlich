import { useState } from "react";
import Markdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import { Link } from "@tanstack/react-router";
import {
  BookOpen,
  Download,
  FileText,
  FlaskConical,
  Loader2,
  Target,
  TestTube,
  Zap,
} from "lucide-react";
import { downloadMarkdown } from "../lib/export-markdown";
import { apiFetch } from "@/shared/lib/api";
import { cn } from "@/shared/lib/utils";
import { SectionHeader } from "@/shared/components/ui/SectionHeader";
import type {
  CandidateRow,
  CostInfo,
  DomainDisplayConfig,
  Experiment,
  Finding,
  Hypothesis,
  NegativeControl,
  ValidationMetricsData,
} from "../types";
import { CandidateTable } from "./CandidateTable";
import { FindingsPanel } from "./FindingsPanel";
import { HypothesisBoard } from "./HypothesisBoard";
import { NegativeControlPanel } from "./NegativeControlPanel";
import { ThreatAssessment } from "./ThreatAssessment";

interface InvestigationReportProps {
  investigationId: string;
  prompt: string;
  summary: string;
  hypotheses: Hypothesis[];
  experiments: Experiment[];
  findings: Finding[];
  candidates: CandidateRow[];
  negativeControls: NegativeControl[];
  cost: CostInfo | null;
  domainConfig?: DomainDisplayConfig | null;
  validationMetrics?: ValidationMetricsData | null;
}

const STATUS_COLORS: Record<string, string> = {
  proposed: "text-muted-foreground",
  testing: "text-accent",
  supported: "text-secondary",
  refuted: "text-destructive",
  revised: "text-primary",
};

export function InvestigationReport({
  investigationId,
  prompt,
  summary,
  hypotheses,
  experiments,
  findings,
  candidates,
  negativeControls,
  cost,
  domainConfig,
  validationMetrics,
}: InvestigationReportProps) {
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      const paper = await apiFetch<Record<string, string>>(
        `/investigate/${investigationId}/paper`,
      );
      const slug = prompt.slice(0, 40).replace(/[^a-zA-Z0-9]+/g, "-").toLowerCase();
      const ts = new Date().toISOString().slice(0, 10);
      downloadMarkdown(paper.full_markdown, `${slug}_${ts}_paper.md`);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Investigation Report
        </h2>
        <div className="flex items-center gap-2">
          <Link
            to="/paper/$id"
            params={{ id: investigationId }}
            className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
          >
            <FileText className="h-3.5 w-3.5" />
            View Paper
          </Link>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-3 py-1.5 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground disabled:opacity-50"
          >
            {exporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            Export Markdown
          </button>
        </div>
      </div>

      {/* 1. Research Question */}
      {prompt && (
        <section className="space-y-3">
          <SectionHeader
            icon={Target}
            title="Research Question"
            description="The original scientific question that initiated this investigation. Defines the domain, target, and scope of scientific discovery."
          />
          <div className="rounded-md border border-border bg-surface p-5">
            <p className="text-sm leading-relaxed">{prompt}</p>
          </div>
        </section>
      )}

      {/* 2. Executive Summary */}
      {summary && (
        <section className="space-y-3">
          <SectionHeader
            icon={BookOpen}
            title="Executive Summary"
            description="AI-generated synthesis of all hypotheses, experiments, and findings. Summarizes conclusions, confidence levels, and recommended next steps."
          />
          <div className="rounded-md border border-border bg-surface p-5">
            <div className="prose prose-sm prose-invert max-w-none prose-headings:text-foreground prose-a:text-primary prose-strong:text-foreground prose-code:text-primary prose-pre:rounded-lg prose-pre:border prose-pre:border-border prose-pre:bg-muted">
              <Markdown rehypePlugins={[rehypeSanitize]}>{summary}</Markdown>
            </div>
          </div>
        </section>
      )}

      {/* 3. Hypotheses -- reuse HypothesisBoard with rich cards (2D mol viewers, confidence bars) */}
      {hypotheses.length > 0 && (
        <section>
          <HypothesisBoard hypotheses={hypotheses} currentHypothesisId="" />
        </section>
      )}

      {/* 4. Methodology -- experiments grouped by hypothesis, following the investigation workflow */}
      {experiments.length > 0 && (
        <section className="space-y-3">
          <SectionHeader
            icon={FlaskConical}
            title={`Methodology (${experiments.length} experiments)`}
            description="Experiments designed and executed to test each hypothesis. Grouped by hypothesis to show the reasoning chain from question to evidence."
          />
          <div className="space-y-3">
            {hypotheses.map((h) => {
              const hExps = experiments.filter((e) => e.hypothesis_id === h.id);
              if (hExps.length === 0) return null;
              const hFindings = findings.filter((f) => f.hypothesis_id === h.id);
              return (
                <div key={h.id} className="rounded-md border border-border bg-surface p-4">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                      Hypothesis {h.id.slice(0, 8)}
                    </span>
                    <span className={cn("font-mono text-[10px] font-medium uppercase", STATUS_COLORS[h.status] ?? "text-muted-foreground")}>
                      {h.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed">{h.statement}</p>
                  <div className="mt-3 space-y-2">
                    {hExps.map((exp) => (
                      <div key={exp.id} className="flex items-start gap-2 rounded-md border border-border/50 bg-muted/10 p-2.5 text-xs text-muted-foreground">
                        <TestTube className="mt-0.5 h-3 w-3 shrink-0 text-primary/70" />
                        <div className="min-w-0">
                          <p className="leading-relaxed text-foreground/80">{exp.description}</p>
                          {exp.tool_count != null && (
                            <p className="mt-1 font-mono text-[10px] text-muted-foreground/50">
                              {exp.tool_count} tool calls, {exp.finding_count ?? 0} findings recorded
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {hFindings.length > 0 && (
                    <div className="mt-2 flex gap-3 font-mono text-[10px]">
                      <span className="text-secondary">{hFindings.filter((f) => f.evidence_type === "supporting").length} supporting</span>
                      <span className="text-destructive">{hFindings.filter((f) => f.evidence_type === "contradicting").length} contradicting</span>
                      <span className="text-muted-foreground">{hFindings.filter((f) => f.evidence_type === "neutral").length} neutral</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 5. Key Findings -- reuse FindingsPanel with evidence cards grouped by hypothesis */}
      <section>
        <FindingsPanel findings={findings} />
      </section>

      {/* 6. Candidates -- reuse CandidateTable with dynamic domain-based columns */}
      <section>
        <CandidateTable candidates={candidates} domainConfig={domainConfig} />
      </section>

      {/* 7. Validity Threats -- causal findings */}
      {(() => {
        const threats = findings
          .filter((f) => f.evidence && typeof f.evidence === "object")
          .flatMap((f) => {
            const ev = f.evidence as unknown as Record<string, unknown>;
            return Array.isArray(ev.threats) ? ev.threats : [];
          })
          .filter(
            (t): t is { type: string; severity: string; description: string; mitigation: string } =>
              typeof t === "object" && t !== null && "type" in t && "severity" in t,
          );
        return threats.length > 0 ? (
          <section>
            <ThreatAssessment threats={threats} />
          </section>
        ) : null;
      })()}

      {/* 8. Model Validation -- reuse NegativeControlPanel with pass/fail icons */}
      {negativeControls.length > 0 && (
        <section className="space-y-3">
          <NegativeControlPanel controls={negativeControls} />
          {validationMetrics && validationMetrics.z_prime != null && (
            <div className="rounded-md border border-border bg-surface p-4">
              <div className="flex items-center gap-3">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                  Z&apos;-factor
                </span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 font-mono text-[10px] font-medium",
                    validationMetrics.z_prime_quality === "excellent"
                      ? "bg-secondary/20 text-secondary"
                      : validationMetrics.z_prime_quality === "marginal"
                        ? "bg-accent/20 text-accent"
                        : "bg-destructive/20 text-destructive",
                  )}
                >
                  {validationMetrics.z_prime.toFixed(3)} ({validationMetrics.z_prime_quality})
                </span>
              </div>
              <div className="mt-2 grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground/60">Positive controls:</span>{" "}
                  <span className="font-mono tabular-nums">
                    mean={validationMetrics.positive_mean.toFixed(3)}, n={validationMetrics.positive_control_count}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground/60">Negative controls:</span>{" "}
                  <span className="font-mono tabular-nums">
                    mean={validationMetrics.negative_mean.toFixed(3)}, n={validationMetrics.negative_control_count}
                  </span>
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* 8. Cost & Performance */}
      {cost && (
        <section className="space-y-3">
          <SectionHeader
            icon={Zap}
            title="Cost & Performance"
            description="Token usage and cost breakdown by model tier. Tracks Director (Opus), Researcher (Sonnet), and Summarizer (Haiku) usage separately."
          />
          <div className="rounded-md border border-border bg-surface p-5">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Input Tokens" value={cost.inputTokens.toLocaleString()} />
              <Stat label="Output Tokens" value={cost.outputTokens.toLocaleString()} />
              <Stat label="Tool Calls" value={cost.toolCalls.toLocaleString()} />
              <Stat label="Total Cost" value={`$${cost.totalCost.toFixed(4)}`} />
            </div>
            {cost.byRole && Object.keys(cost.byRole).length > 0 && (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground/70">
                      <th className="pb-2 pr-4">Role</th>
                      <th className="pb-2 pr-4">Model</th>
                      <th className="pb-2 pr-4">Input</th>
                      <th className="pb-2 pr-4">Output</th>
                      <th className="pb-2 pr-4">Calls</th>
                      <th className="pb-2">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(cost.byRole).map(([role, mc]) => (
                      <tr key={role} className="border-b border-border/50 last:border-0">
                        <td className="py-2 pr-4 font-mono capitalize">{role}</td>
                        <td className="py-2 pr-4 font-mono text-muted-foreground/70">{mc.model_display}</td>
                        <td className="py-2 pr-4 font-mono tabular-nums">{mc.input_tokens.toLocaleString()}</td>
                        <td className="py-2 pr-4 font-mono tabular-nums">{mc.output_tokens.toLocaleString()}</td>
                        <td className="py-2 pr-4 font-mono tabular-nums">{mc.calls}</td>
                        <td className="py-2 font-mono tabular-nums">${mc.cost_usd.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">{label}</p>
      <p className="mt-0.5 font-mono text-sm font-medium tabular-nums">{value}</p>
    </div>
  );
}

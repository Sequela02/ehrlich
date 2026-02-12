import { useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FlaskConical,
  Lightbulb,
  Shrink,
  TestTube,
  Wrench,
  XCircle,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { SSEEvent } from "../types";

interface TimelineProps {
  events: SSEEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (events.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        Connecting to investigation stream...
      </div>
    );
  }

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  return (
    <div className="space-y-0.5">
      {events.map((event, i) => (
        <TimelineEntry
          key={i}
          event={event}
          isExpanded={expanded.has(i)}
          onToggle={() => toggle(i)}
        />
      ))}
    </div>
  );
}

function ExpandToggle({
  isExpanded,
  onClick,
  className,
}: {
  isExpanded: boolean;
  onClick: () => void;
  className?: string;
}) {
  const Icon = isExpanded ? ChevronDown : ChevronRight;
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={cn(
        "inline-flex shrink-0 items-center rounded p-0.5 text-muted-foreground/50 transition-colors hover:text-muted-foreground",
        className,
      )}
    >
      <Icon className="h-3 w-3" />
    </button>
  );
}

function TimelineEntry({
  event,
  isExpanded,
  onToggle,
}: {
  event: SSEEvent;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  switch (event.event) {
    case "hypothesis_formulated":
      return (
        <div className="mt-4 mb-2 flex items-center gap-2 rounded-md bg-accent/8 px-3 py-2 text-sm font-medium text-accent first:mt-0">
          <Lightbulb className="h-4 w-4" />
          <span className="flex-1 truncate">
            {event.data.statement as string}
          </span>
          {(event.data.parent_id as string) && (
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground">
              revised
            </span>
          )}
        </div>
      );

    case "experiment_started":
      return (
        <div className="mt-3 mb-1 flex items-center gap-2 rounded-md bg-primary/8 px-3 py-2 text-xs font-medium text-primary">
          <FlaskConical className="h-3.5 w-3.5" />
          {event.data.description as string}
        </div>
      );

    case "experiment_completed":
      return (
        <div className="mt-1 mb-2 flex items-center gap-2 border-t border-b border-border/20 px-3 py-2.5 text-xs">
          <CheckCircle2 className="h-3.5 w-3.5 text-primary/50" />
          <span className="font-medium text-primary/60">Experiment complete</span>
          <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground/50">
            {event.data.tool_count as number} tools
            <span className="mx-1.5 text-border">|</span>
            {event.data.finding_count as number} findings
          </span>
        </div>
      );

    case "hypothesis_evaluated": {
      const status = event.data.status as string;
      const confidence = event.data.confidence as number;
      const reasoning = event.data.reasoning as string;
      const statusColor =
        status === "supported"
          ? "text-secondary"
          : status === "refuted"
            ? "text-destructive"
            : "text-accent";
      return (
        <div
          className="my-1 cursor-pointer rounded-md border border-border/30 px-3 py-2"
          onClick={onToggle}
        >
          <div className="flex items-center gap-2 text-xs">
            <TestTube className={cn("h-3.5 w-3.5", statusColor)} />
            <span className={cn("font-medium", statusColor)}>
              {status.toUpperCase()}
            </span>
            {confidence > 0 && (
              <span className="font-mono text-[10px] text-muted-foreground">
                {(confidence * 100).toFixed(0)}% confidence
              </span>
            )}
            {reasoning && (
              <ExpandToggle isExpanded={isExpanded} onClick={onToggle} className="ml-auto" />
            )}
          </div>
          {isExpanded && reasoning && (
            <p className="mt-1.5 pl-5 text-[11px] italic leading-relaxed text-muted-foreground">
              {reasoning}
            </p>
          )}
        </div>
      );
    }

    case "negative_control": {
      const correct = event.data.correctly_classified as boolean;
      return (
        <div className="my-0.5 flex items-center gap-2 rounded px-3 py-1 text-xs">
          {correct ? (
            <CheckCircle2 className="h-3 w-3 text-secondary" />
          ) : (
            <XCircle className="h-3 w-3 text-destructive" />
          )}
          <span className="font-mono text-muted-foreground/70">
            {(event.data.name as string) || "Control"}
          </span>
          <span className="font-mono text-[10px] text-muted-foreground/50">
            score: {(event.data.score as number)?.toFixed(3)}
          </span>
        </div>
      );
    }

    case "tool_called":
      return (
        <div className="group flex items-center gap-2 rounded px-3 py-1 transition-colors hover:bg-muted/30">
          <Wrench className="h-3 w-3 shrink-0 text-muted-foreground/40" />
          <span className="font-mono text-xs font-medium text-foreground/70">
            {event.data.tool_name as string}
          </span>
          <span className="truncate font-mono text-[11px] text-muted-foreground/40">
            {formatToolInput(event.data.tool_input as Record<string, unknown>)}
          </span>
        </div>
      );

    case "tool_result": {
      const result = event.data.result_preview as string;
      const toolName = event.data.tool_name as string;
      const summary = summarizeToolResult(toolName, result);
      return (
        <div
          className="ml-7 cursor-pointer rounded border-l border-border/40 px-2.5 py-0.5 hover:bg-muted/20"
          onClick={onToggle}
        >
          <div className="flex items-center gap-1.5">
            <ExpandToggle
              isExpanded={isExpanded}
              onClick={onToggle}
            />
            <span className="text-[11px] text-muted-foreground/50">
              {summary}
            </span>
          </div>
          {isExpanded && (
            <pre className="mt-1 max-h-60 overflow-auto whitespace-pre-wrap break-all rounded bg-muted/20 p-2 font-mono text-[10px] leading-relaxed text-muted-foreground/40">
              {formatJsonPreview(result)}
            </pre>
          )}
        </div>
      );
    }

    case "finding_recorded": {
      const evidence = event.data.evidence as string | undefined;
      const evidenceType = (event.data.evidence_type as string) || "neutral";
      const typeColor =
        evidenceType === "supporting"
          ? "text-secondary"
          : evidenceType === "contradicting"
            ? "text-destructive"
            : "text-muted-foreground";
      return (
        <div className="my-1.5 rounded-md border border-primary/20 bg-primary/5 px-3 py-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
            {event.data.title as string}
            <span className={cn("ml-auto rounded bg-muted px-1.5 py-0.5 font-mono text-[9px]", typeColor)}>
              {evidenceType}
            </span>
          </div>
          {(event.data.detail as string) && (
            <p className="mt-1 pl-5 text-[11px] leading-relaxed text-foreground/60">
              {event.data.detail as string}
            </p>
          )}
          {evidence && (
            <div className="mt-1.5 ml-5 rounded bg-muted/30 px-2 py-1">
              <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground/50">
                Evidence
              </span>
              <p className="mt-0.5 text-[10px] leading-relaxed text-muted-foreground/70">
                {evidence}
              </p>
            </div>
          )}
        </div>
      );
    }

    case "thinking": {
      const text = event.data.text as string;
      const isLong = text.length > 150;
      return (
        <div
          className={cn(
            "rounded px-3 py-1 text-[11px] italic leading-relaxed text-foreground/30",
            isLong && "cursor-pointer hover:text-foreground/40",
          )}
          onClick={isLong ? onToggle : undefined}
        >
          {isLong && (
            <ExpandToggle
              isExpanded={isExpanded}
              onClick={onToggle}
              className="mr-1"
            />
          )}
          <span className={isExpanded ? "" : "line-clamp-2"}>{text}</span>
        </div>
      );
    }

    case "output_summarized":
      return (
        <div className="ml-7 flex items-center gap-1.5 border-l border-border/40 px-2.5 py-0.5 font-mono text-[10px] text-muted-foreground/30">
          <Shrink className="h-2.5 w-2.5" />
          {event.data.tool_name as string}:{" "}
          {event.data.original_length as number}
          {" -> "}
          {event.data.summarized_length as number} chars
        </div>
      );

    case "literature_survey_completed": {
      const pico = event.data.pico as Record<string, string> | undefined;
      const grade = event.data.evidence_grade as string;
      const queries = event.data.search_queries as number;
      const total = event.data.total_results as number;
      const included = event.data.included_results as number;
      const gradeColor =
        grade === "high"
          ? "bg-secondary/20 text-secondary"
          : grade === "moderate"
            ? "bg-accent/20 text-accent"
            : grade === "low"
              ? "bg-orange-500/20 text-orange-400"
              : "bg-destructive/20 text-destructive";
      return (
        <div
          className="my-2 cursor-pointer rounded-md border border-primary/30 bg-primary/5 px-3 py-2"
          onClick={onToggle}
        >
          <div className="flex items-center gap-2 text-xs font-medium text-primary">
            <BookOpen className="h-3.5 w-3.5 shrink-0" />
            Literature Survey Complete
            <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground/50">
              {queries} queries | {total} found | {included} included
            </span>
            {grade && (
              <span className={cn("rounded px-1.5 py-0.5 font-mono text-[9px] uppercase", gradeColor)}>
                {grade}
              </span>
            )}
            <ExpandToggle isExpanded={isExpanded} onClick={onToggle} />
          </div>
          {isExpanded && pico && (
            <div className="mt-2 flex flex-wrap gap-1.5 pl-5">
              {Object.entries(pico).map(([key, value]) =>
                key !== "search_terms" && value ? (
                  <span
                    key={key}
                    className="rounded bg-muted/40 px-2 py-0.5 text-[10px] text-muted-foreground"
                  >
                    <span className="font-medium uppercase tracking-wider">{key[0]}</span>: {value}
                  </span>
                ) : null,
              )}
            </div>
          )}
        </div>
      );
    }

    case "error":
      return (
        <div className="my-1 flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          <XCircle className="h-3.5 w-3.5 shrink-0" />
          {event.data.error as string}
        </div>
      );

    case "completed":
      return (
        <div className="mt-3 flex items-center gap-2 rounded-md bg-primary/10 px-3 py-2.5 text-sm font-medium text-primary">
          <CheckCircle2 className="h-4 w-4" />
          Investigation complete ({event.data.candidate_count as number}{" "}
          candidates)
        </div>
      );

    default:
      return null;
  }
}

function summarizeToolResult(toolName: string, raw: string): string {
  try {
    const data = JSON.parse(raw) as Record<string, unknown>;

    if (data.error) return `Error: ${truncate(String(data.error), 80)}`;

    if (
      (toolName === "search_literature" || toolName === "search_papers") &&
      Array.isArray(data.papers)
    ) {
      const count = data.papers.length;
      const first = (data.papers[0] as Record<string, unknown>)?.title;
      return first
        ? `${count} papers -- "${truncate(String(first), 60)}"`
        : `${count} papers found`;
    }

    if (toolName === "explore_dataset" && typeof data.size === "number") {
      return `${data.size} compounds (${data.active_count ?? 0} active)`;
    }

    if (
      toolName === "analyze_substructures" &&
      typeof data.significant_count === "number"
    ) {
      return `${data.significant_count} significant substructures of ${(data.enrichments as unknown[])?.length ?? 0} tested`;
    }

    if (data.model_id || data.model_type) {
      const score = typeof data.roc_auc === "number" ? ` (AUC: ${(data.roc_auc as number).toFixed(3)})` : "";
      return `Model trained${score}`;
    }

    if (
      toolName === "predict_candidates" &&
      Array.isArray(data.candidates)
    ) {
      return `${data.candidates.length} candidates predicted`;
    }

    if (toolName === "dock_against_target" && data.score != null) {
      return `Docking score: ${data.score}`;
    }

    if (toolName === "predict_admet") {
      return "ADMET profile computed";
    }

    if (data.status === "recorded") {
      return `Finding recorded: ${truncate(String(data.title ?? ""), 60)}`;
    }

    if (data.status === "concluded") {
      return `Concluded with ${data.candidate_count ?? 0} candidates`;
    }

    const keys = Object.keys(data).slice(0, 4).join(", ");
    return keys ? `{${keys}${Object.keys(data).length > 4 ? ", ..." : ""}}` : raw.slice(0, 80);
  } catch {
    return truncate(raw, 80);
  }
}

function formatJsonPreview(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

function formatToolInput(input: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(input)) {
    if (typeof value === "string") {
      parts.push(`${key}="${truncate(value, 40)}"`);
    } else if (Array.isArray(value)) {
      parts.push(`${key}=[${value.length} items]`);
    } else {
      parts.push(`${key}=${String(value)}`);
    }
  }
  return parts.join(", ");
}

function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "...";
}

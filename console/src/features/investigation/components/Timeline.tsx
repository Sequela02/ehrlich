import { useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FlaskConical,
  Lightbulb,
  TestTube,
  Wrench,
  Activity,
  AlertCircle
} from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { SSEEvent } from "../types";
import { Badge } from "@/shared/components/ui/badge";

interface TimelineProps {
  events: SSEEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (events.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center text-sm text-muted-foreground">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
          <Activity className="h-5 w-5 animate-pulse text-primary" />
        </div>
        <p>Connecting to investigation stream...</p>
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
    <div className="space-y-3 pl-1 pr-2">
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
        "inline-flex shrink-0 items-center justify-center rounded-sm h-5 w-5 hover:bg-muted text-muted-foreground transition-colors",
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" />
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
        <div className="group relative flex gap-3 pb-2">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-500 ring-1 ring-amber-500/20">
            <Lightbulb className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-foreground/80">Hypothesis Formulated</span>
              {(event.data.parent_id as string) && (
                <Badge variant="outline" className="h-5 px-1.5 text-[9px] text-muted-foreground font-normal">Revised</Badge>
              )}
            </div>
            <p className="text-sm text-foreground leading-relaxed">{event.data.statement as string}</p>
          </div>
        </div>
      );

    case "experiment_started":
      return (
        <div className="group relative flex gap-3 pb-2.">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-blue-500 ring-1 ring-blue-500/20">
            <FlaskConical className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 space-y-0.5">
            <span className="text-xs font-medium text-foreground/70">Experiment Started</span>
            <p className="text-xs text-muted-foreground">{event.data.description as string}</p>
          </div>
        </div>
      );

    case "experiment_completed":
      return (
        <div className="group relative flex gap-3 py-1">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-green-500 ring-1 ring-green-500/20">
            <CheckCircle2 className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 flex items-center justify-between">
            <span className="text-xs font-medium text-foreground/70">Experiment Completed</span>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <Badge variant="secondary" className="h-5 px-1.5 font-mono text-[9px]">{event.data.tool_count as number} tools</Badge>
              <Badge variant="secondary" className="h-5 px-1.5 font-mono text-[9px]">{event.data.finding_count as number} findings</Badge>
            </div>
          </div>
        </div>
      );

    case "hypothesis_evaluated": {
      const status = event.data.status as string;
      const confidence = event.data.confidence as number;
      const reasoning = event.data.reasoning as string;
      const variant = status === "supported" ? "default" : status === "refuted" ? "destructive" : "secondary";

      return (
        <div className="group relative flex gap-3 py-1">
          <div className={cn(
            "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ring-1",
            status === "supported" ? "bg-primary/10 ring-primary/20 text-primary" :
              status === "refuted" ? "bg-destructive/10 ring-destructive/20 text-destructive" :
                "bg-muted ring-border text-muted-foreground"
          )}>
            <TestTube className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2 cursor-pointer hover:opacity-80" onClick={onToggle}>
              <Badge variant={variant as any} className="uppercase text-[10px] h-5 tracking-wide">{status}</Badge>
              {confidence > 0 && <span className="text-[10px] text-muted-foreground font-mono">{(confidence * 100).toFixed(0)}% conf</span>}
              {reasoning && <ExpandToggle isExpanded={isExpanded} onClick={onToggle} className="ml-auto" />}
            </div>
            {isExpanded && reasoning && (
              <div className="text-xs text-muted-foreground italic bg-muted/30 p-2 rounded-md border border-border/50">
                {reasoning}
              </div>
            )}
          </div>
        </div>
      );
    }

    case "negative_control": {
      const correct = event.data.correctly_classified as boolean;
      return (
        <div className="flex items-center gap-2 py-1 pl-9">
          {correct ? (
            <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50 h-5 text-[10px]">PASS</Badge>
          ) : (
            <Badge variant="destructive" className="h-5 text-[10px]">FAIL</Badge>
          )}
          <span className="text-xs font-mono text-muted-foreground">{(event.data.name as string) || "Control"}</span>
          <span className="text-[10px] text-muted-foreground/50 font-mono ml-auto">score: {(event.data.score as number)?.toFixed(3)}</span>
        </div>
      );
    }

    case "tool_called":
      return (
        <div className="flex items-center gap-2 py-1 pl-9 group">
          <Wrench className="h-3 w-3 text-muted-foreground/30" />
          <span className="text-xs font-mono text-foreground/70">{event.data.tool_name as string}</span>
          <span className="text-[10px] text-muted-foreground/40 font-mono truncate max-w-[150px]">
            {formatToolInput(event.data.tool_input as Record<string, unknown>)}
          </span>
        </div>
      );

    case "tool_result": {
      const result = event.data.result_preview as string;
      const toolName = event.data.tool_name as string;
      const summary = summarizeToolResult(toolName, result);
      return (
        <div className="pl-9 py-0.5">
          <div
            className="flex items-start gap-1.5 cursor-pointer hover:bg-muted/50 rounded p-1 -ml-1 transition-colors"
            onClick={onToggle}
          >
            <ExpandToggle isExpanded={isExpanded} onClick={onToggle} className="mt-0.5" />
            <span className="text-[11px] text-muted-foreground leading-tight">{summary}</span>
          </div>
          {isExpanded && (
            <div className="mt-1 overflow-hidden rounded-md border border-border/50 bg-muted/20">
              <pre className="max-h-60 overflow-auto p-2 text-[10px] font-mono text-muted-foreground/70 custom-scrollbar">
                {formatJsonPreview(result)}
              </pre>
            </div>
          )}
        </div>
      );
    }

    case "finding_recorded": {
      const evidence = event.data.evidence as string | undefined;
      const evidenceType = (event.data.evidence_type as string) || "neutral";
      const typeColor =
        evidenceType === "supporting"
          ? "border-green-200 bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 dark:border-green-900/50"
          : evidenceType === "contradicting"
            ? "border-red-200 bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/50"
            : "border-border bg-muted/30 text-muted-foreground";

      return (
        <div className={cn("mx-1 my-2 rounded-md border p-3", typeColor)}>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">{event.data.title as string}</span>
                <Badge variant="outline" className="bg-transparent border-current/20 h-5 text-[9px] uppercase opacity-70">
                  {evidenceType}
                </Badge>
              </div>
              {(event.data.detail as string) && (
                <p className="text-xs opacity-90 leading-relaxed">{event.data.detail as string}</p>
              )}
              {evidence && (
                <div className="mt-2 text-[10px] font-mono bg-black/5 dark:bg-white/5 rounded p-2 italic opacity-80">
                  {evidence}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    case "thinking": {
      const text = event.data.text as string;
      const isLong = text.length > 150;
      return (
        <div className="pl-9 py-1 text-[11px] text-muted-foreground/60 italic">
          <div className={cn("flex gap-2", isLong && "cursor-pointer hover:text-muted-foreground")} onClick={isLong ? onToggle : undefined}>
            <span className={isExpanded ? "" : "line-clamp-2"}>{text}</span>
            {isLong && <ExpandToggle isExpanded={isExpanded} onClick={onToggle} className="h-4 w-4" />}
          </div>
        </div>
      );
    }

    case "output_summarized":
      return null; // Hide noise from timeline for cleaner UI

    case "literature_survey_completed": {
      const grade = event.data.evidence_grade as string;
      const total = event.data.total_results as number;
      const included = event.data.included_results as number;
      const pico = event.data.pico as Record<string, string> | undefined;

      return (
        <div className="group relative flex gap-3 py-2">
          <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-purple-500/10 text-purple-500 ring-1 ring-purple-500/20">
            <BookOpen className="h-3.5 w-3.5" />
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between cursor-pointer hover:opacity-80" onClick={onToggle}>
              <span className="text-xs font-semibold text-foreground/80">Literature Survey</span>
              <div className="flex gap-2">
                <Badge variant="outline" className="h-5 text-[9px] font-mono">{included}/{total} papers</Badge>
                {grade && <Badge variant="secondary" className="h-5 text-[9px] uppercase">{grade} Grade</Badge>}
                <ExpandToggle isExpanded={isExpanded} onClick={onToggle} />
              </div>
            </div>
            {isExpanded && pico && (
              <div className="bg-muted/30 p-2 rounded-md border border-border/50 text-[10px] space-y-1">
                {Object.entries(pico).map(([k, v]) => (
                  v && k !== 'search_terms' && <div key={k}><strong className="uppercase text-muted-foreground">{k[0]}:</strong> <span className="text-foreground/70">{v}</span></div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    case "error":
      return (
        <div className="my-2 flex gap-3 rounded-md bg-destructive/5 p-3 text-destructive border border-destructive/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wide">Error Occurred</h4>
            <p className="text-xs opacity-90">{event.data.error as string}</p>
          </div>
        </div>
      );

    case "phase_changed":
      return (
        <div className="my-3 border-t border-border pt-3">
          <span className="font-mono text-[10px] uppercase tracking-wider text-primary/60">
            Phase {event.data.phase as number}: {event.data.name as string}
          </span>
        </div>
      );

    case "completed":
      return (
        <div className="mt-6 flex flex-col items-center justify-center gap-2 rounded-lg border border-primary/20 bg-primary/5 p-6 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20 text-primary mb-2">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="font-semibold text-primary">Investigation Complete</h3>
          <p className="text-xs text-muted-foreground">
            Candidate identification process finished with {event.data.candidate_count as number} candidates found.
          </p>
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
      return `${count} papers analyzed`;
    }

    if (toolName === "explore_dataset" && typeof data.size === "number") {
      return `${data.size} compounds (${data.active_count ?? 0} active)`;
    }

    // ... rest of summarizers can be simplified ...
    if (data.status === "recorded") return `Finding recorded`;

    return "Result available";
  } catch {
    return "Result raw output";
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
  return Object.keys(input).map(k => k).join(", ");
}

function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "...";
}

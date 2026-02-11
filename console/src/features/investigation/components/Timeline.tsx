import {
  BookOpen,
  Brain,
  CheckCircle2,
  FlaskConical,
  Microscope,
  Search,
  Shrink,
  Sparkles,
  Target,
  Wrench,
  XCircle,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { SSEEvent } from "../types";

interface TimelineProps {
  events: SSEEvent[];
  currentPhase: string;
}

const PHASE_ICONS: Record<string, typeof FlaskConical> = {
  "Literature Review": BookOpen,
  "Data Exploration": Search,
  "Model Training": Brain,
  "Virtual Screening": Target,
  "Structural Analysis": Microscope,
  "Resistance Assessment": FlaskConical,
  Conclusions: CheckCircle2,
};

export function Timeline({ events, currentPhase }: TimelineProps) {
  if (events.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        Connecting to investigation stream...
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {currentPhase && (
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-primary">
          <PhaseIcon phase={currentPhase} />
          {currentPhase}
        </div>
      )}
      {events.map((event, i) => (
        <TimelineEntry key={i} event={event} />
      ))}
    </div>
  );
}

function PhaseIcon({ phase }: { phase: string }) {
  const Icon = PHASE_ICONS[phase] ?? FlaskConical;
  return <Icon className="h-4 w-4" />;
}

function TimelineEntry({ event }: { event: SSEEvent }) {
  switch (event.event) {
    case "phase_started":
      return (
        <div className="flex items-center gap-2 rounded-md bg-primary/5 px-3 py-2 text-sm font-medium text-primary">
          <PhaseIcon phase={event.data.phase as string} />
          {event.data.phase as string}
        </div>
      );

    case "tool_called":
      return (
        <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-muted-foreground">
          <Wrench className="h-3.5 w-3.5 shrink-0" />
          <span className="font-mono font-medium">{event.data.tool_name as string}</span>
          <span className="truncate text-muted-foreground/60">
            {formatToolInput(event.data.tool_input as Record<string, unknown>)}
          </span>
        </div>
      );

    case "tool_result":
      return (
        <div className="px-3 py-1 pl-9 text-xs text-muted-foreground/80">
          <span className="line-clamp-2">{truncate(event.data.result_preview as string, 200)}</span>
        </div>
      );

    case "finding_recorded":
      return (
        <div className="rounded-md border border-secondary/20 bg-secondary/5 px-3 py-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-secondary">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Finding: {event.data.title as string}
          </div>
          {(event.data.detail as string) && (
            <p className="mt-1 pl-5 text-xs text-muted-foreground">
              {truncate(event.data.detail as string, 300)}
            </p>
          )}
        </div>
      );

    case "thinking":
      return (
        <div className="px-3 py-1.5 text-xs leading-relaxed text-foreground/70">
          {truncate(event.data.text as string, 500)}
        </div>
      );

    case "director_planning": {
      const stage = event.data.stage as string;
      const phase = event.data.phase as string;
      const label =
        stage === "planning"
          ? "Director planning investigation..."
          : stage === "review"
            ? `Director reviewing ${phase}...`
            : "Director synthesizing results...";
      return (
        <div className="flex items-center gap-2 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-xs font-medium text-amber-600 dark:text-amber-400">
          <Brain className="h-3.5 w-3.5 animate-pulse" />
          {label}
        </div>
      );
    }

    case "director_decision": {
      const stage = event.data.stage as string;
      const decision = event.data.decision as Record<string, unknown>;
      const summary =
        stage === "review" && typeof decision.quality_score === "number"
          ? `Quality: ${(decision.quality_score as number * 100).toFixed(0)}% — ${decision.proceed ? "Proceeding" : "Stopping"}`
          : stage === "planning"
            ? `Plan: ${((decision.phases as unknown[]) ?? []).length} phases`
            : stage === "synthesis"
              ? `Synthesis: ${((decision.candidates as unknown[]) ?? []).length} candidates`
              : "Decision received";
      return (
        <div className="rounded-md border border-amber-500/20 px-3 py-1.5 text-xs text-amber-600 dark:text-amber-400">
          <Sparkles className="mr-1.5 inline h-3 w-3" />
          {summary}
        </div>
      );
    }

    case "output_summarized":
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 pl-9 text-[10px] text-muted-foreground/60">
          <Shrink className="h-3 w-3" />
          {event.data.tool_name as string}: {event.data.original_length as number} chars
          {" -> "}{event.data.summarized_length as number} chars
        </div>
      );

    case "error":
      return (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          <XCircle className="h-3.5 w-3.5 shrink-0" />
          {event.data.error as string}
        </div>
      );

    case "completed":
      return (
        <div className={cn(
          "flex items-center gap-2 rounded-md bg-secondary/10 px-3 py-2",
          "text-sm font-medium text-secondary",
        )}>
          <CheckCircle2 className="h-4 w-4" />
          Investigation complete ({event.data.candidate_count as number} candidates)
        </div>
      );

    default:
      return null;
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

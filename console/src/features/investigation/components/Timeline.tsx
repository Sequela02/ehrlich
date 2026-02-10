import {
  BookOpen,
  Brain,
  CheckCircle2,
  FlaskConical,
  Microscope,
  Search,
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

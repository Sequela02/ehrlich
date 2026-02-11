import { useState } from "react";
import {
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
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
    <div className="space-y-1.5">
      {currentPhase && (
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-primary">
          <PhaseIcon phase={currentPhase} />
          {currentPhase}
        </div>
      )}
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

function PhaseIcon({ phase }: { phase: string }) {
  const Icon = PHASE_ICONS[phase] ?? FlaskConical;
  return <Icon className="h-4 w-4" />;
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
    case "phase_started":
      return (
        <div className="flex items-center gap-2 rounded-md bg-primary/10 px-3 py-2 text-sm font-medium text-primary">
          <PhaseIcon phase={event.data.phase as string} />
          {event.data.phase as string}
        </div>
      );

    case "tool_called":
      return (
        <div className="flex items-center gap-2 px-3 py-1 text-xs text-muted-foreground">
          <Wrench className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60" />
          <span className="font-mono font-medium text-primary/80">
            {event.data.tool_name as string}
          </span>
          <span className="truncate font-mono text-muted-foreground/50">
            {formatToolInput(event.data.tool_input as Record<string, unknown>)}
          </span>
        </div>
      );

    case "tool_result": {
      const result = event.data.result_preview as string;
      const isLong = result.length > 150;
      return (
        <div
          className={cn(
            "px-3 py-0.5 pl-9 font-mono text-[11px] text-muted-foreground/50",
            isLong && "cursor-pointer",
          )}
          onClick={isLong ? onToggle : undefined}
        >
          {isLong && (
            <ExpandToggle
              isExpanded={isExpanded}
              onClick={onToggle}
              className="mr-1 -ml-4"
            />
          )}
          <span className={isExpanded ? "" : "line-clamp-2"}>{result}</span>
        </div>
      );
    }

    case "finding_recorded": {
      const evidence = event.data.evidence as string | undefined;
      return (
        <div className="rounded-md border-l-2 border-primary bg-primary/5 px-3 py-2">
          <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Finding: {event.data.title as string}
          </div>
          {(event.data.detail as string) && (
            <p className="mt-1 pl-5 text-xs leading-relaxed text-muted-foreground">
              {event.data.detail as string}
            </p>
          )}
          {evidence && (
            <div className="mt-1.5 ml-5 rounded bg-muted/30 px-2 py-1.5">
              <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
                Evidence
              </span>
              <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                {evidence}
              </p>
            </div>
          )}
        </div>
      );
    }

    case "thinking": {
      const text = event.data.text as string;
      const isLong = text.length > 200;
      return (
        <div
          className={cn(
            "px-3 py-1.5 text-xs italic leading-relaxed text-foreground/50",
            isLong && "cursor-pointer",
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
          <span className={isExpanded ? "" : "line-clamp-3"}>{text}</span>
        </div>
      );
    }

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
        <div className="flex items-center gap-2 rounded-md bg-accent/10 px-3 py-2 text-xs font-medium text-accent">
          <Brain className="h-3.5 w-3.5 animate-pulse" />
          {label}
        </div>
      );
    }

    case "director_decision": {
      const stage = event.data.stage as string;
      const decision = event.data.decision as Record<string, unknown>;
      return (
        <DirectorDecisionCard
          stage={stage}
          decision={decision}
          isExpanded={isExpanded}
          onToggle={onToggle}
        />
      );
    }

    case "output_summarized":
      return (
        <div className="flex items-center gap-1.5 px-3 py-0.5 pl-9 font-mono text-[10px] text-muted-foreground/40">
          <Shrink className="h-3 w-3" />
          {event.data.tool_name as string}: {event.data.original_length as number} chars
          {" -> "}
          {event.data.summarized_length as number} chars
        </div>
      );

    case "phase_completed":
      return (
        <div className="my-2 flex items-center gap-2 border-t border-b border-border/50 px-3 py-2 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3.5 w-3.5 text-primary/60" />
          <span className="font-medium text-primary/70">
            {event.data.phase as string}
          </span>
          <span>complete</span>
          <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground/60">
            {event.data.tool_count as number} tools, {event.data.finding_count as number} findings
          </span>
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
        <div
          className={cn(
            "flex items-center gap-2 rounded-md bg-primary/10 px-3 py-2",
            "text-sm font-medium text-primary",
          )}
        >
          <CheckCircle2 className="h-4 w-4" />
          Investigation complete ({event.data.candidate_count as number}{" "}
          candidates)
        </div>
      );

    default:
      return null;
  }
}

function DirectorDecisionCard({
  stage,
  decision,
  isExpanded,
  onToggle,
}: {
  stage: string;
  decision: Record<string, unknown>;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  let header: string;
  if (stage === "planning") {
    const phases = (decision.phases as unknown[]) ?? [];
    header = `Plan: ${phases.length} phases`;
  } else if (stage === "review" && typeof decision.quality_score === "number") {
    const pct = (decision.quality_score as number) * 100;
    header = `Quality: ${pct.toFixed(0)}% — ${decision.proceed ? "Proceeding" : "Stopping"}`;
  } else if (stage === "synthesis") {
    const cands = (decision.candidates as unknown[]) ?? [];
    header = `Synthesis: ${cands.length} candidates`;
  } else {
    header = "Decision received";
  }

  return (
    <div className="border-l-2 border-accent/40 px-3 py-1.5">
      <div
        className="flex cursor-pointer items-center gap-1.5 font-mono text-xs text-accent"
        onClick={onToggle}
      >
        <ExpandToggle isExpanded={isExpanded} onClick={onToggle} />
        <Sparkles className="h-3 w-3" />
        {header}
      </div>
      {isExpanded && (
        <div className="mt-2 space-y-1.5 pl-5 text-xs text-muted-foreground">
          {stage === "planning" && <PlanningDetail decision={decision} />}
          {stage === "review" && <ReviewDetail decision={decision} />}
          {stage === "synthesis" && <SynthesisDetail decision={decision} />}
        </div>
      )}
    </div>
  );
}

function PlanningDetail({ decision }: { decision: Record<string, unknown> }) {
  const phases = (decision.phases as Array<Record<string, unknown>>) ?? [];
  const focusAreas = (decision.focus_areas as string[]) ?? [];
  return (
    <>
      {phases.map((p, i) => (
        <div key={i} className="rounded bg-muted/20 px-2 py-1">
          <span className="font-medium text-foreground/70">
            {(p.name as string) || `Phase ${i + 1}`}
          </span>
          {(p.goals as string[])?.length > 0 && (
            <div className="mt-0.5 pl-2 text-[11px] text-muted-foreground/70">
              {(p.goals as string[]).map((g, j) => (
                <div key={j}>- {g}</div>
              ))}
            </div>
          )}
        </div>
      ))}
      {focusAreas.length > 0 && (
        <div className="text-[11px]">
          <span className="font-mono uppercase text-muted-foreground/50">
            Focus:{" "}
          </span>
          {focusAreas.join(", ")}
        </div>
      )}
    </>
  );
}

function ReviewDetail({ decision }: { decision: Record<string, unknown> }) {
  const keyFindings = (decision.key_findings as string[]) ?? [];
  const gaps = (decision.gaps as string[]) ?? [];
  const guidance = decision.next_phase_guidance as string | undefined;
  return (
    <>
      {keyFindings.length > 0 && (
        <div>
          <span className="font-mono text-[10px] uppercase text-muted-foreground/50">
            Key findings
          </span>
          {keyFindings.map((f, i) => (
            <div key={i} className="pl-2 text-[11px]">
              - {f}
            </div>
          ))}
        </div>
      )}
      {gaps.length > 0 && (
        <div>
          <span className="font-mono text-[10px] uppercase text-muted-foreground/50">
            Gaps
          </span>
          {gaps.map((g, i) => (
            <div key={i} className="pl-2 text-[11px] text-accent/70">
              - {g}
            </div>
          ))}
        </div>
      )}
      {guidance && (
        <div className="text-[11px]">
          <span className="font-mono uppercase text-muted-foreground/50">
            Next:{" "}
          </span>
          {guidance}
        </div>
      )}
    </>
  );
}

function SynthesisDetail({ decision }: { decision: Record<string, unknown> }) {
  const confidence = decision.confidence as string | undefined;
  const limitations = (decision.limitations as string[]) ?? [];
  return (
    <>
      {confidence && (
        <div className="text-[11px]">
          <span className="font-mono uppercase text-muted-foreground/50">
            Confidence:{" "}
          </span>
          <span
            className={cn(
              confidence === "high" && "text-primary",
              confidence === "medium" && "text-accent",
              confidence === "low" && "text-destructive",
            )}
          >
            {confidence}
          </span>
        </div>
      )}
      {limitations.length > 0 && (
        <div>
          <span className="font-mono text-[10px] uppercase text-muted-foreground/50">
            Limitations
          </span>
          {limitations.map((l, i) => (
            <div key={i} className="pl-2 text-[11px]">
              - {l}
            </div>
          ))}
        </div>
      )}
    </>
  );
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

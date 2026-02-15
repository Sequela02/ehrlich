import { useEffect, useRef, useState, type ReactNode } from "react";
import { Check, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface PhaseSectionProps {
  phaseNumber: number;
  currentPhase: number;
  completed: boolean;
  title: string;
  summaryContent: ReactNode;
  children: ReactNode;
  defaultExpanded?: boolean;
}

export function PhaseSection({
  phaseNumber,
  currentPhase,
  completed,
  title,
  summaryContent,
  children,
  defaultExpanded = false,
}: PhaseSectionProps) {
  const effectiveCurrentPhase = completed ? 7 : currentPhase;
  const isCompleted = phaseNumber < effectiveCurrentPhase;
  const isActive = phaseNumber === effectiveCurrentPhase;
  const isPending = phaseNumber > effectiveCurrentPhase;

  const [expanded, setExpanded] = useState(defaultExpanded);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isActive && sectionRef.current) {
      sectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [isActive]);

  if (isPending) return null;

  if (isCompleted) {
    return (
      <div className="rounded-md border border-border/50 bg-surface/50">
        <button
          onClick={() => setExpanded((p) => !p)}
          className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/30"
        >
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Check className="h-3.5 w-3.5" />
          </div>
          <span className="font-mono text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {title}
          </span>
          <span className="ml-2 flex-1 text-xs text-muted-foreground/60">
            {summaryContent}
          </span>
          {expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground/40" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/40" />
          )}
        </button>
        {expanded && (
          <div className="border-t border-border/50 px-4 py-4">{children}</div>
        )}
      </div>
    );
  }

  // Active phase
  return (
    <div ref={sectionRef} className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary">
          <span className="font-mono text-[10px] font-bold">{phaseNumber}</span>
        </div>
        <span className="font-mono text-xs font-medium uppercase tracking-wider text-primary">
          {title}
        </span>
        <div className={cn("h-px flex-1 bg-primary/20")} />
      </div>
      {children}
    </div>
  );
}

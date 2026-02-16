import { cn } from "@/shared/lib/utils";
import type { PhaseInfo } from "../types";

const PHASES = [
  { number: 1, label: "Classification" },
  { number: 2, label: "Literature" },
  { number: 3, label: "Formulation" },
  { number: 4, label: "Testing" },
  { number: 5, label: "Controls" },
  { number: 6, label: "Synthesis" },
];

interface PhaseProgressProps {
  phase: PhaseInfo | null;
  completed: boolean;
}

export function PhaseProgress({ phase, completed }: PhaseProgressProps) {
  const currentNumber = completed ? 7 : (phase?.phase ?? 0);

  return (
    <div className="shrink-0 border-b border-border px-4 py-3 lg:px-6">
      <div className="flex items-center gap-1">
        {PHASES.map((p, i) => (
          <div key={p.number} className="flex flex-1 items-center">
            <div
              className={cn(
                "h-1.5 w-full rounded-full transition-colors",
                p.number < currentNumber
                  ? "bg-primary"
                  : p.number === currentNumber
                    ? "animate-pulse bg-primary"
                    : "bg-muted",
              )}
            />
            {i < PHASES.length - 1 && <div className="w-1 shrink-0" />}
          </div>
        ))}
      </div>
      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {PHASES.map((p) => (
            <span
              key={p.number}
              className={cn(
                "hidden font-mono text-[10px] tracking-wider sm:inline",
                p.number < currentNumber
                  ? "text-primary/60"
                  : p.number === currentNumber
                    ? "font-medium text-primary"
                    : "text-muted-foreground/40",
              )}
            >
              {p.label}
            </span>
          ))}
        </div>
        <span className="font-mono text-[10px] text-muted-foreground/60">
          {completed
            ? "Investigation Complete"
            : phase
              ? phase.description
              : "Initializing..."}
        </span>
      </div>
    </div>
  );
}

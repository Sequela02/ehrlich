import { cn } from "@/shared/lib/utils";

const PHASES = [
  "Literature Review",
  "Data Exploration",
  "Model Training",
  "Virtual Screening",
  "Structural Analysis",
  "Resistance Assessment",
  "Conclusions",
];

interface PhaseProgressProps {
  currentPhase: string;
  completedPhases: string[];
}

export function PhaseProgress({
  currentPhase,
  completedPhases,
}: PhaseProgressProps) {
  if (!currentPhase && completedPhases.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center pb-6">
      {PHASES.map((phase, index) => {
        const isActive = phase === currentPhase;
        const isCompleted =
          completedPhases.includes(phase) ||
          (currentPhase !== phase &&
            PHASES.indexOf(phase) < PHASES.indexOf(currentPhase));
        const isLast = index === PHASES.length - 1;

        return (
          <div key={phase} className="group flex flex-1 items-center">
            {/* Node */}
            <div className="relative flex flex-col items-center">
              <div
                className={cn(
                  "h-2.5 w-2.5 rounded-full transition-all",
                  isActive && "bg-primary animate-pulse-glow",
                  isCompleted && "bg-primary",
                  !isActive && !isCompleted && "border border-border bg-muted",
                )}
              />
              <span
                className={cn(
                  "absolute top-5 whitespace-nowrap font-mono text-[10px]",
                  isActive && "text-primary animate-pulse-glow",
                  isCompleted && "text-primary/70",
                  !isActive && !isCompleted && "text-muted-foreground/50",
                )}
              >
                {phase.split(" ")[0]}
              </span>
            </div>
            {/* Bond line */}
            {!isLast && (
              <div
                className={cn(
                  "h-px flex-1 transition-colors",
                  isCompleted ? "bg-primary/50" : "bg-border",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

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
    <div className="flex items-center gap-1">
      {PHASES.map((phase) => {
        const isActive = phase === currentPhase;
        const isCompleted =
          completedPhases.includes(phase) ||
          (currentPhase !== phase &&
            PHASES.indexOf(phase) < PHASES.indexOf(currentPhase));

        return (
          <div
            key={phase}
            className="group relative flex-1"
            title={phase}
          >
            <div
              className={cn(
                "h-1.5 rounded-full transition-all",
                isActive && "animate-pulse bg-primary",
                isCompleted && "bg-secondary",
                !isActive && !isCompleted && "bg-muted",
              )}
            />
            <span
              className={cn(
                "absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] opacity-0",
                "transition-opacity group-hover:opacity-100",
                isActive && "text-primary",
                isCompleted && "text-secondary",
                !isActive && !isCompleted && "text-muted-foreground",
              )}
            >
              {phase.split(" ")[0]}
            </span>
          </div>
        );
      })}
    </div>
  );
}

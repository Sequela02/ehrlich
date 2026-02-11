import {
  BookOpen,
  Brain,
  CheckCircle2,
  FlaskConical,
  Microscope,
  Search,
  Target,
  Wrench,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";

const PHASE_ICONS: Record<string, typeof FlaskConical> = {
  "Literature Review": BookOpen,
  "Data Exploration": Search,
  "Model Training": Brain,
  "Virtual Screening": Target,
  "Structural Analysis": Microscope,
  "Resistance Assessment": FlaskConical,
  Conclusions: CheckCircle2,
};

interface ActivePhaseCardProps {
  currentPhase: string;
  completed: boolean;
  activeToolName: string;
  phaseToolCount: number;
  phaseFindingCount: number;
}

export function ActivePhaseCard({
  currentPhase,
  completed,
  activeToolName,
  phaseToolCount,
  phaseFindingCount,
}: ActivePhaseCardProps) {
  if (completed) return null;

  // Between phases: director reviewing
  if (!currentPhase) {
    return (
      <div className="relative overflow-hidden rounded-lg border border-accent/30 bg-accent/5 p-4">
        <div className="absolute inset-0 animate-pulse rounded-lg border border-accent/20" />
        <div className="relative flex items-center gap-3">
          <Brain className="h-5 w-5 animate-pulse text-accent" />
          <div>
            <p className="text-sm font-medium text-accent">
              Director reviewing...
            </p>
            <p className="text-xs text-muted-foreground">
              Preparing next phase
            </p>
          </div>
        </div>
      </div>
    );
  }

  const PhaseIcon = PHASE_ICONS[currentPhase] ?? FlaskConical;

  return (
    <div className="relative overflow-hidden rounded-lg border border-primary/30 bg-primary/5 p-4">
      <div className="absolute inset-0 animate-pulse rounded-lg border border-primary/10" />
      <div className="relative flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <PhaseIcon className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-medium text-primary">{currentPhase}</p>
            {activeToolName ? (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Wrench className="h-3 w-3 animate-spin text-primary/60" />
                <span className="font-mono">{activeToolName}</span>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Processing...</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span
            className={cn(
              "font-mono tabular-nums",
              phaseToolCount > 0 && "text-primary/70",
            )}
          >
            {phaseToolCount} {phaseToolCount === 1 ? "tool" : "tools"}
          </span>
          <span className="text-border">|</span>
          <span
            className={cn(
              "font-mono tabular-nums",
              phaseFindingCount > 0 && "text-primary/70",
            )}
          >
            {phaseFindingCount}{" "}
            {phaseFindingCount === 1 ? "finding" : "findings"}
          </span>
        </div>
      </div>
    </div>
  );
}

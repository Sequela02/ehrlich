import { useState } from "react";
import { ChevronDown, ChevronRight, Shield } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface Threat {
  type: string;
  severity: string;
  description: string;
  mitigation: string;
}

interface ThreatAssessmentProps {
  threats: Threat[];
}

const SEVERITY_STYLES: Record<string, { badge: string; border: string }> = {
  high: {
    badge: "bg-destructive/20 text-destructive",
    border: "border-destructive/30",
  },
  medium: {
    badge: "bg-accent/20 text-accent",
    border: "border-accent/30",
  },
  low: {
    badge: "bg-primary/20 text-primary",
    border: "border-primary/30",
  },
};

function ThreatRow({ threat }: { threat: Threat }) {
  const [expanded, setExpanded] = useState(false);
  const styles = SEVERITY_STYLES[threat.severity] ?? SEVERITY_STYLES.low;

  return (
    <div className={cn("border-b border-border/50 last:border-0", styles.border)}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted/20"
      >
        {expanded ? (
          <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" />
        )}
        <span className={cn("rounded-full px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase", styles.badge)}>
          {threat.severity}
        </span>
        <span className="font-mono text-[10px] text-muted-foreground/70">
          {threat.type.replace(/_/g, " ")}
        </span>
        <span className="ml-auto truncate text-foreground/80">{threat.description}</span>
      </button>
      {expanded && (
        <div className="border-t border-border/30 bg-muted/10 px-3 py-2 pl-8 text-xs text-muted-foreground">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
            Mitigation:
          </span>{" "}
          {threat.mitigation}
        </div>
      )}
    </div>
  );
}

export function ThreatAssessment({ threats }: ThreatAssessmentProps) {
  if (threats.length === 0) return null;

  // Sort: high first, then medium, then low
  const order: Record<string, number> = { high: 0, medium: 1, low: 2 };
  const sorted = [...threats].sort(
    (a, b) => (order[a.severity] ?? 3) - (order[b.severity] ?? 3),
  );

  const highCount = threats.filter((t) => t.severity === "high").length;
  const medCount = threats.filter((t) => t.severity === "medium").length;

  return (
    <div className="space-y-3">
      <div>
        <h3 className="border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
          <Shield className="mr-1.5 inline-block h-3.5 w-3.5" />
          Validity Threats ({threats.length})
        </h3>
        <p className="mt-1 pl-4 text-xs leading-relaxed text-muted-foreground/50">
          {highCount > 0 && (
            <span className="text-destructive">{highCount} high severity</span>
          )}
          {highCount > 0 && medCount > 0 && ", "}
          {medCount > 0 && (
            <span className="text-accent">{medCount} medium severity</span>
          )}
          {(highCount > 0 || medCount > 0) && " -- "}
          Threats to internal validity identified during causal analysis.
        </p>
      </div>
      <div className="overflow-hidden rounded-md border border-border">
        {sorted.map((threat, i) => (
          <ThreatRow key={`${threat.type}-${i}`} threat={threat} />
        ))}
      </div>
    </div>
  );
}

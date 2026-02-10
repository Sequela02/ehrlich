import { FileText } from "lucide-react";
import type { Finding } from "../types";

interface FindingsPanelProps {
  findings: Finding[];
}

export function FindingsPanel({ findings }: FindingsPanelProps) {
  if (findings.length === 0) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground">Findings</h3>
        <p className="text-xs text-muted-foreground">
          Findings will appear as the investigation progresses.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-muted-foreground">
        Findings ({findings.length})
      </h3>
      <div className="space-y-2">
        {findings.map((f, i) => (
          <div key={i} className="rounded-lg border border-border p-3">
            <div className="flex items-start gap-2">
              <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-secondary" />
              <div className="min-w-0">
                <p className="text-xs font-medium">{f.title}</p>
                {f.phase && (
                  <span className="mt-0.5 inline-block rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {f.phase}
                  </span>
                )}
                {f.detail && (
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                    {f.detail.length > 200 ? f.detail.slice(0, 200) + "..." : f.detail}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

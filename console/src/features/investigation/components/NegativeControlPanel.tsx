import { CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { NegativeControl } from "../types";

interface NegativeControlPanelProps {
  controls: NegativeControl[];
}

export function NegativeControlPanel({ controls }: NegativeControlPanelProps) {
  if (controls.length === 0) return null;

  const correct = controls.filter((c) => c.correctly_classified).length;

  return (
    <div className="space-y-3">
      <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Negative Controls ({correct}/{controls.length} correct)
      </h3>
      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-3 py-2 text-left font-mono font-medium text-muted-foreground">
                Compound
              </th>
              <th className="px-3 py-2 text-right font-mono font-medium text-muted-foreground">
                Score
              </th>
              <th className="px-3 py-2 text-center font-mono font-medium text-muted-foreground">
                Result
              </th>
            </tr>
          </thead>
          <tbody>
            {controls.map((nc, i) => (
              <tr key={i} className="border-b border-border/50 last:border-0">
                <td className="px-3 py-2">
                  <div className="font-medium">{nc.name || "Unknown"}</div>
                  <div className="font-mono text-[10px] text-muted-foreground">
                    {nc.smiles.length > 30
                      ? nc.smiles.slice(0, 30) + "..."
                      : nc.smiles}
                  </div>
                </td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">
                  {nc.prediction_score.toFixed(3)}
                </td>
                <td className="px-3 py-2 text-center">
                  {nc.correctly_classified ? (
                    <CheckCircle2
                      className={cn("mx-auto h-4 w-4 text-secondary")}
                    />
                  ) : (
                    <XCircle className="mx-auto h-4 w-4 text-destructive" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

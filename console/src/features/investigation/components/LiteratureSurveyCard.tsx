import { Badge } from "@/shared/components/ui/badge";
import type { LiteratureSurveyCompletedData } from "../types";

const PICO_COLORS: Record<string, string> = {
  population: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  intervention: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  comparator: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  outcome: "bg-green-500/10 text-green-500 border-green-500/20",
};

interface LiteratureSurveyCardProps {
  data: LiteratureSurveyCompletedData;
}

export function LiteratureSurveyCard({ data }: LiteratureSurveyCardProps) {
  const picoEntries = Object.entries(data.pico).filter(
    ([k, v]) => v && k !== "search_terms",
  );

  return (
    <div className="space-y-3">
      {picoEntries.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {picoEntries.map(([key, value]) => (
            <div
              key={key}
              className={`rounded-md border px-3 py-1.5 ${PICO_COLORS[key] ?? "bg-muted text-muted-foreground border-border"}`}
            >
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
                {key[0]}
              </span>
              <span className="ml-2 text-xs">{value}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <span className="font-mono text-xs text-muted-foreground">
          {data.included_results}/{data.total_results} papers included
        </span>
        <span className="text-muted-foreground/30">|</span>
        <span className="font-mono text-xs text-muted-foreground">
          {data.search_queries} queries
        </span>
        {data.evidence_grade && (
          <>
            <span className="text-muted-foreground/30">|</span>
            <Badge variant="secondary" className="h-5 text-[10px] uppercase">
              {data.evidence_grade} Grade
            </Badge>
          </>
        )}
      </div>

      {data.assessment && (
        <p className="text-xs leading-relaxed text-muted-foreground">
          {data.assessment}
        </p>
      )}
    </div>
  );
}

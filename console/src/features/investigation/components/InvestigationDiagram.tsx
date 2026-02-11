import { lazy, Suspense, useMemo } from "react";
import { Loader2 } from "lucide-react";
import {
  buildDiagramElements,
  type HypothesisNode,
  type ExperimentNode,
  type FindingNode,
} from "../lib/diagram-builder";

const ExcalidrawWrapper = lazy(() => import("./ExcalidrawWrapper"));

interface InvestigationDiagramProps {
  hypotheses: HypothesisNode[];
  experiments: ExperimentNode[];
  findings: FindingNode[];
  completed: boolean;
}

export function InvestigationDiagram({
  hypotheses,
  experiments,
  findings,
  completed,
}: InvestigationDiagramProps) {
  const skeletons = useMemo(
    () => buildDiagramElements(hypotheses, experiments, findings),
    [hypotheses, experiments, findings],
  );

  if (hypotheses.length === 0) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-lg border border-border bg-[#0f1219]">
        <p className="text-sm text-muted-foreground/50">
          No hypotheses to diagram yet
        </p>
      </div>
    );
  }

  return (
    <div className="h-[500px] overflow-hidden rounded-lg border border-border">
      <Suspense
        fallback={
          <div className="flex h-full items-center justify-center bg-[#0f1219]">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        }
      >
        <ExcalidrawWrapper
          skeletons={skeletons}
          viewMode={!completed}
        />
      </Suspense>
    </div>
  );
}

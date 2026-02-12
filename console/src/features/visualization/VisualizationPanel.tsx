import { Suspense } from 'react';
import { getVizComponent, type VizPayload } from './VizRegistry';
import { VIZ_COLORS } from './theme';

interface VisualizationPanelProps {
  visualizations: VizPayload[];
}

function VizFallback() {
  return (
    <div
      className="flex h-48 items-center justify-center rounded-lg border border-border"
      style={{ background: VIZ_COLORS.background }}
    >
      <span className="font-mono text-xs" style={{ color: VIZ_COLORS.neutral }}>
        Loading chart...
      </span>
    </div>
  );
}

function VizCard({ payload }: { payload: VizPayload }) {
  const Component = getVizComponent(payload.viz_type);
  if (!Component) {
    return (
      <div
        className="rounded-lg border border-border p-4"
        style={{ background: VIZ_COLORS.background }}
      >
        <span className="font-mono text-xs" style={{ color: VIZ_COLORS.neutral }}>
          Unknown visualization type: {payload.viz_type}
        </span>
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border border-border p-4"
      style={{ background: VIZ_COLORS.background }}
    >
      <Suspense fallback={<VizFallback />}>
        <Component data={payload.data} title={payload.title} />
      </Suspense>
    </div>
  );
}

export default function VisualizationPanel({ visualizations }: VisualizationPanelProps) {
  if (visualizations.length === 0) return null;

  return (
    <section className="space-y-3">
      <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Visualizations
      </h3>
      <div className="grid gap-4 lg:grid-cols-2">
        {visualizations.map((viz, i) => (
          <VizCard key={`${viz.viz_type}-${i}`} payload={viz} />
        ))}
      </div>
    </section>
  );
}

import { Suspense, useMemo } from 'react';
import { getVizComponent, type VizPayload } from './VizRegistry';
import { VIZ_COLORS } from './theme';
import { MOLECULAR_TOOL_NAMES } from '@/features/investigation/lib/scene-builder';
import { ErrorBoundary } from '@/features/shared/components/ErrorBoundary';
import { LiveLabViewer } from '@/features/investigation/components/LiveLabViewer';
import type { SSEEvent, Experiment } from '@/features/investigation/types';

interface VisualizationPanelProps {
  visualizations: VizPayload[];
  events?: SSEEvent[];
  experiments?: Experiment[];
  completed?: boolean;
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

export default function VisualizationPanel({
  visualizations,
  events,
  experiments,
  completed,
}: VisualizationPanelProps) {
  const hasMolecularData = useMemo(() => {
    if (!events) return false;
    return events.some(
      (e) =>
        (e.event === 'tool_called' || e.event === 'tool_result') &&
        MOLECULAR_TOOL_NAMES.has((e.data as Record<string, unknown>).tool_name as string),
    );
  }, [events]);

  const showLab = hasMolecularData && events != null;
  const hasCharts = visualizations.length > 0;

  if (!showLab && !hasCharts) return null;

  return (
    <section className="space-y-3">
      <h3 className="border-l-2 border-primary pl-3 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Visualizations
      </h3>

      {showLab && (
        <div>
          <p className="mb-2 pl-3 text-[11px] leading-relaxed text-muted-foreground/50">
            Real-time 3D molecular visualization as structures are analyzed.
          </p>
          <ErrorBoundary fallbackMessage="Failed to load 3D viewer">
            <LiveLabViewer
              events={events}
              completed={completed ?? false}
              experiments={experiments}
            />
          </ErrorBoundary>
        </div>
      )}

      {hasCharts && (
        <div className="grid gap-4 lg:grid-cols-2">
          {visualizations.map((viz, i) => (
            <VizCard key={`${viz.viz_type}-${i}`} payload={viz} />
          ))}
        </div>
      )}
    </section>
  );
}

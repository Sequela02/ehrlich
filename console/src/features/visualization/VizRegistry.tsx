import { lazy, type ComponentType } from 'react';

/**
 * Payload shape matching backend VisualizationRendered event.
 */
export interface VizPayload {
  viz_type: string;
  title: string;
  data: Record<string, unknown>;
  config: Record<string, unknown>;
  domain?: string;
  experiment_id?: string;
}

/**
 * Props that every chart component receives.
 * `data` and `title` come directly from the VizPayload.
 */
interface ChartProps {
  data: Record<string, unknown>;
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

type ChartComponent = ComponentType<ChartProps>;

const registry = new Map<string, ChartComponent>();

// Lazy-load chart components to keep initial bundle small
const LazyBindingScatter = lazy(() => import('./charts/BindingScatter'));
const LazyADMETRadar = lazy(() => import('./charts/ADMETRadar'));
const LazyTrainingTimeline = lazy(() => import('./charts/TrainingTimeline'));
const LazyForestPlot = lazy(() => import('./charts/ForestPlot'));
const LazyEvidenceMatrix = lazy(() => import('./charts/EvidenceMatrix'));
const LazyBodyDiagram = lazy(() => import('./anatomy/BodyDiagram'));

registry.set('binding_scatter', LazyBindingScatter as unknown as ChartComponent);
registry.set('admet_radar', LazyADMETRadar as unknown as ChartComponent);
registry.set('training_timeline', LazyTrainingTimeline as unknown as ChartComponent);
registry.set('forest_plot', LazyForestPlot as unknown as ChartComponent);
registry.set('evidence_matrix', LazyEvidenceMatrix as unknown as ChartComponent);
registry.set('muscle_heatmap', LazyBodyDiagram as unknown as ChartComponent);

/**
 * Look up a chart component by viz_type string.
 * Returns undefined for unknown types.
 */
export function getVizComponent(vizType: string): ChartComponent | undefined {
  return registry.get(vizType);
}

/**
 * List all registered viz types.
 */
export function getRegisteredVizTypes(): string[] {
  return Array.from(registry.keys());
}

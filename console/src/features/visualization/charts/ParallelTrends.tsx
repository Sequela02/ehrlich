import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface SeriesPoint {
  period: string;
  value: number;
}

interface ParallelTrendsProps {
  data: {
    treatment: SeriesPoint[];
    control: SeriesPoint[];
    treatment_start: string;
  };
  title: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.value.toFixed(2)}
        </p>
      ))}
    </div>
  );
}

export default function ParallelTrends({ data, title }: ParallelTrendsProps) {
  // Merge treatment and control into a single dataset keyed by period
  const allPeriods = new Set([
    ...data.treatment.map((t) => t.period),
    ...data.control.map((c) => c.period),
  ]);
  const treatmentMap = new Map(data.treatment.map((t) => [t.period, t.value]));
  const controlMap = new Map(data.control.map((c) => [c.period, c.value]));

  const periods = Array.from(allPeriods).sort();
  const merged = periods.map((period) => ({
    period,
    treatment: treatmentMap.get(period),
    control: controlMap.get(period),
  }));

  // Find the index of treatment_start for shading
  const startIdx = periods.indexOf(data.treatment_start);
  const lastPeriod = periods[periods.length - 1];

  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={merged} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={VIZ_COLORS.grid} />
          <XAxis
            dataKey="period"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          {data.treatment_start && startIdx >= 0 && lastPeriod && (
            <ReferenceArea
              x1={data.treatment_start}
              x2={lastPeriod}
              fill={VIZ_COLORS.primary}
              fillOpacity={0.06}
              label={{
                value: 'Post-treatment',
                fill: VIZ_COLORS.neutral,
                fontSize: 9,
                position: 'insideTopRight',
              }}
            />
          )}
          {data.treatment_start && (
            <ReferenceLine
              x={data.treatment_start}
              stroke={VIZ_COLORS.text}
              strokeDasharray="4 3"
              label={{
                value: 'Treatment',
                fill: VIZ_COLORS.text,
                fontSize: 10,
                position: 'top',
              }}
            />
          )}
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontFamily: 'monospace', fontSize: 10, color: VIZ_COLORS.text }}
          />
          <Line
            dataKey="treatment"
            name="Treatment"
            stroke={VIZ_COLORS.primary}
            strokeWidth={2}
            dot={{ r: 3, fill: VIZ_COLORS.primary }}
            connectNulls
          />
          <Line
            dataKey="control"
            name="Control"
            stroke={VIZ_COLORS.neutral}
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ r: 3, fill: VIZ_COLORS.neutral }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

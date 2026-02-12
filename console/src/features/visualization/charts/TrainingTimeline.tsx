import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  Brush,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface TimelineEntry {
  date: string;
  load: number;
  acwr?: number;
}

interface TrainingTimelineProps {
  data: {
    timeline: TimelineEntry[];
    acwr: Array<{ date: string; value: number }>;
    danger_zones: Array<{ min: number; max: number; label: string }>;
  };
  title: string;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ dataKey: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey}: {p.value.toFixed(2)}
        </p>
      ))}
    </div>
  );
}

export default function TrainingTimeline({ data, title }: TrainingTimelineProps) {
  const acwrMap = new Map(data.acwr.map((a) => [a.date, a.value]));
  const merged = data.timeline.map((t) => ({
    ...t,
    acwr: t.acwr ?? acwrMap.get(t.date),
  }));

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
            dataKey="date"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            yAxisId="load"
            orientation="left"
            label={{ value: 'Load', angle: -90, position: 'insideLeft', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            yAxisId="acwr"
            orientation="right"
            label={{ value: 'ACWR', angle: 90, position: 'insideRight', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          {data.danger_zones.map((dz) => (
            <ReferenceArea
              key={dz.label}
              yAxisId="acwr"
              y1={dz.min}
              y2={dz.max}
              fill={VIZ_COLORS.danger}
              fillOpacity={0.1}
              label={{ value: dz.label, fill: VIZ_COLORS.danger, fontSize: 9 }}
            />
          ))}
          <Tooltip content={<CustomTooltip />} />
          <Bar
            yAxisId="load"
            dataKey="load"
            fill={VIZ_COLORS.primary}
            fillOpacity={0.7}
            radius={[2, 2, 0, 0]}
          />
          <Line
            yAxisId="acwr"
            dataKey="acwr"
            stroke={VIZ_COLORS.danger}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Brush
            dataKey="date"
            height={20}
            stroke={VIZ_COLORS.neutral}
            fill={VIZ_COLORS.background}
            travellerWidth={8}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

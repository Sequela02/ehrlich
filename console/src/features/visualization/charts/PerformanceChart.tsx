import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  Brush,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface PerformanceChartProps {
  data: {
    points: Array<{ day: number; fitness: number; fatigue: number; form: number }>;
    peak_form: number;
    form_zones: Array<{ min: number; max: number; label: string }>;
  };
  title: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="mb-1 font-semibold">Day {label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey === 'fitness' ? 'CTL' : p.dataKey === 'fatigue' ? 'ATL' : 'TSB'}:{' '}
          {p.value.toFixed(1)}
        </p>
      ))}
    </div>
  );
}

export default function PerformanceChart({ data, title }: PerformanceChartProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={data.points} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={VIZ_COLORS.grid} />
          <XAxis
            dataKey="day"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            label={{ value: 'Day', position: 'insideBottom', offset: -10, fill: VIZ_COLORS.neutral, fontSize: 11 }}
          />
          <YAxis
            yAxisId="load"
            orientation="left"
            label={{ value: 'CTL / ATL', angle: -90, position: 'insideLeft', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            yAxisId="form"
            orientation="right"
            label={{ value: 'TSB (Form)', angle: 90, position: 'insideRight', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          {data.form_zones.map((zone) => (
            <ReferenceArea
              key={zone.label}
              yAxisId="form"
              y1={zone.min}
              y2={zone.max}
              fill={zone.min >= 0 ? VIZ_COLORS.secondary : VIZ_COLORS.danger}
              fillOpacity={0.1}
              label={{ value: zone.label, fill: zone.min >= 0 ? VIZ_COLORS.secondary : VIZ_COLORS.danger, fontSize: 9 }}
            />
          ))}
          <ReferenceLine yAxisId="form" y={0} stroke={VIZ_COLORS.neutral} strokeDasharray="4 3" />
          <Tooltip content={<CustomTooltip />} />
          <Line
            yAxisId="load"
            dataKey="fitness"
            stroke={VIZ_COLORS.secondary}
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            connectNulls
          />
          <Line
            yAxisId="load"
            dataKey="fatigue"
            stroke={VIZ_COLORS.danger}
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            connectNulls
          />
          <Line
            yAxisId="form"
            dataKey="form"
            stroke={VIZ_COLORS.primary}
            strokeWidth={2.5}
            dot={false}
            connectNulls
          />
          <Brush
            dataKey="day"
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

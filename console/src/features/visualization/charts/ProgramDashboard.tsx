import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface IndicatorEntry {
  name: string;
  baseline: number;
  target: number;
  actual: number;
  unit: string;
  pct_target: number;
  status: 'on_track' | 'at_risk' | 'off_track';
}

interface ProgramDashboardProps {
  data: {
    program_name: string;
    indicators: IndicatorEntry[];
  };
  title: string;
}

const STATUS_COLORS: Record<string, string> = {
  on_track: VIZ_COLORS.primary,
  at_risk: VIZ_COLORS.warning,
  off_track: VIZ_COLORS.danger,
};

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: IndicatorEntry & { pct_display: number } }>;
}) {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="font-semibold">{d.name}</p>
      <p>
        Baseline: {d.baseline} {d.unit}
      </p>
      <p>
        Target: {d.target} {d.unit}
      </p>
      <p>
        Actual: {d.actual} {d.unit}
      </p>
      <p style={{ color: STATUS_COLORS[d.status] }}>
        {Math.round(d.pct_target * 100)}% of target
      </p>
    </div>
  );
}

export default function ProgramDashboard({ data, title }: ProgramDashboardProps) {
  const chartData = data.indicators.map((ind) => ({
    ...ind,
    pct_display: Math.round(ind.pct_target * 100),
  }));

  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between">
        <h4
          className="font-mono text-xs font-medium uppercase tracking-wider"
          style={{ color: VIZ_COLORS.text }}
        >
          {title}
        </h4>
        <span
          className="rounded border px-2 py-0.5 font-mono text-xs"
          style={{
            color: VIZ_COLORS.text,
            borderColor: VIZ_COLORS.grid,
            background: VIZ_COLORS.surface,
          }}
        >
          {data.program_name}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(200, data.indicators.length * 40 + 40)}>
        <BarChart data={chartData} layout="vertical">
          <XAxis
            type="number"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            domain={[0, 'auto']}
            label={{
              value: '% Target',
              position: 'insideBottom',
              fill: VIZ_COLORS.neutral,
              fontSize: 10,
              offset: -5,
            }}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            width={120}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={100} stroke={VIZ_COLORS.text} strokeDasharray="4 3" />
          <ReferenceLine x={80} stroke={VIZ_COLORS.warning} strokeDasharray="2 4" strokeOpacity={0.5} />
          <Bar dataKey="pct_display" name="% Target">
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={STATUS_COLORS[entry.status]} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

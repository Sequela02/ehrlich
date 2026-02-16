import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface Region {
  name: string;
  value: number;
}

interface GeographicComparisonProps {
  data: {
    regions: Region[];
    metric_name: string;
    benchmark: number | null;
  };
  title: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.[0]) return null;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="font-semibold">{label}</p>
      <p>{payload[0].value.toFixed(2)}</p>
    </div>
  );
}

export default function GeographicComparison({ data, title }: GeographicComparisonProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data.regions}>
          <XAxis
            dataKey="name"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            label={{
              value: data.metric_name,
              angle: -90,
              position: 'insideLeft',
              fill: VIZ_COLORS.neutral,
              fontSize: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          {data.benchmark != null && (
            <ReferenceLine
              y={data.benchmark}
              stroke={VIZ_COLORS.warning}
              strokeDasharray="4 3"
              label={{
                value: `Benchmark: ${data.benchmark}`,
                fill: VIZ_COLORS.warning,
                fontSize: 10,
                position: 'right',
              }}
            />
          )}
          <Bar
            dataKey="value"
            fill={VIZ_COLORS.primary}
            fillOpacity={0.8}
            radius={[2, 2, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

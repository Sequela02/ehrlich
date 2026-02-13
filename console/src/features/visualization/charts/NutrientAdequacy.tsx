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

interface NutrientEntry {
  name: string;
  pct_rda: number;
  status: 'deficient' | 'inadequate' | 'adequate';
  intake: number;
  rda: number;
  unit: string;
}

interface NutrientAdequacyProps {
  data: {
    nutrients: NutrientEntry[];
    mar_score: number;
  };
  title: string;
}

const STATUS_COLORS: Record<string, string> = {
  deficient: VIZ_COLORS.danger,
  inadequate: VIZ_COLORS.warning,
  adequate: VIZ_COLORS.secondary,
};

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: NutrientEntry & { pct_display: number } }>;
}) {
  if (!active || !payload?.[0]) return null;
  const n = payload[0].payload;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="font-semibold">{n.name}</p>
      <p>
        {n.intake} / {n.rda} {n.unit}
      </p>
      <p>{Math.round(n.pct_rda * 100)}% RDA</p>
      <p style={{ color: STATUS_COLORS[n.status] }}>{n.status}</p>
    </div>
  );
}

export default function NutrientAdequacy({ data, title }: NutrientAdequacyProps) {
  const chartData = data.nutrients.map((n) => ({
    ...n,
    pct_display: Math.round(n.pct_rda * 100),
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
          MAR: {(data.mar_score * 100).toFixed(1)}%
        </span>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(200, data.nutrients.length * 32 + 40)}>
        <BarChart data={chartData} layout="vertical">
          <XAxis
            type="number"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            domain={[0, 'auto']}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            width={100}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={100} stroke={VIZ_COLORS.text} strokeDasharray="4 3" />
          <Bar dataKey="pct_display" name="% RDA">
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={STATUS_COLORS[entry.status]} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

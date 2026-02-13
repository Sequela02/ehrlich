import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface Nutrient {
  name: string;
  amount: number;
  unit: string;
  pct_rda: number;
}

interface Food {
  name: string;
  nutrients: Nutrient[];
}

interface NutrientComparisonProps {
  data: {
    foods: Food[];
    nutrient_labels: string[];
  };
  title: string;
}

const BAR_COLORS = [
  VIZ_COLORS.primary,
  VIZ_COLORS.secondary,
  VIZ_COLORS.warning,
  VIZ_COLORS.danger,
];

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
      <p className="font-semibold">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {entry.value.toFixed(1)}% RDA
        </p>
      ))}
    </div>
  );
}

export default function NutrientComparison({ data, title }: NutrientComparisonProps) {
  // Reshape: one row per nutrient, one key per food
  const chartData = data.nutrient_labels.map((nutrient) => {
    const row: Record<string, string | number> = { nutrient };
    for (const food of data.foods) {
      const match = food.nutrients.find((n) => n.name === nutrient);
      row[food.name] = match ? Math.round(match.pct_rda * 100) : 0;
    }
    return row;
  });

  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData}>
          <XAxis
            dataKey="nutrient"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
            label={{
              value: '% RDA',
              angle: -90,
              position: 'insideLeft',
              fill: VIZ_COLORS.neutral,
              fontSize: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontFamily: 'monospace', fontSize: 10, color: VIZ_COLORS.text }}
          />
          {data.foods.map((food, i) => (
            <Bar
              key={food.name}
              dataKey={food.name}
              fill={BAR_COLORS[i % BAR_COLORS.length]}
              fillOpacity={0.8}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface ScatterPoint {
  name: string;
  x: number;
  y: number;
  smiles?: string;
}

interface BindingScatterProps {
  data: {
    points: ScatterPoint[];
    x_label: string;
    y_label: string;
  };
  title: string;
  onPointClick?: (point: { name: string; smiles?: string }) => void;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ScatterPoint }> }) {
  if (!active || !payload?.[0]) return null;
  const pt = payload[0].payload;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="mb-1 font-semibold">{pt.name}</p>
      <p>x: {pt.x.toFixed(3)}</p>
      <p>y: {pt.y.toFixed(3)}</p>
    </div>
  );
}

export default function BindingScatter({ data, title, onPointClick }: BindingScatterProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={VIZ_COLORS.grid} />
          <XAxis
            dataKey="x"
            type="number"
            name={data.x_label}
            label={{ value: data.x_label, position: 'bottom', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <YAxis
            dataKey="y"
            type="number"
            name={data.y_label}
            label={{ value: data.y_label, angle: -90, position: 'insideLeft', fill: VIZ_COLORS.neutral, fontSize: 11 }}
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
            stroke={VIZ_COLORS.grid}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter
            data={data.points}
            fill={VIZ_COLORS.primary}
            fillOpacity={0.7}
            onClick={(entry: { payload?: ScatterPoint }) => {
              if (onPointClick && entry.payload) {
                onPointClick({ name: entry.payload.name, smiles: entry.payload.smiles });
              }
            }}
            cursor="pointer"
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

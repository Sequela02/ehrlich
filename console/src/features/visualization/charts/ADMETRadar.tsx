import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { VIZ_COLORS } from '../theme';

interface ADMETRadarProps {
  data: {
    compound: string;
    properties: Array<{ axis: string; value: number }>;
  };
  title: string;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { axis: string; value: number } }> }) {
  if (!active || !payload?.[0]) return null;
  const pt = payload[0].payload;
  return (
    <div
      className="rounded-md border border-border px-3 py-2 font-mono text-xs shadow-lg"
      style={{ background: VIZ_COLORS.surface, color: VIZ_COLORS.text }}
    >
      <p className="font-semibold">{pt.axis}</p>
      <p>{pt.value.toFixed(3)}</p>
    </div>
  );
}

export default function ADMETRadar({ data, title }: ADMETRadarProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title} -- {data.compound}
      </h4>
      <ResponsiveContainer width="100%" height={350}>
        <RadarChart data={data.properties} outerRadius="75%">
          <PolarGrid stroke={VIZ_COLORS.grid} />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 10 }}
          />
          <PolarRadiusAxis
            tick={{ fill: VIZ_COLORS.neutral, fontSize: 9 }}
            stroke={VIZ_COLORS.grid}
          />
          <Tooltip content={<CustomTooltip />} />
          <Radar
            dataKey="value"
            stroke={VIZ_COLORS.primary}
            fill={VIZ_COLORS.primary}
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

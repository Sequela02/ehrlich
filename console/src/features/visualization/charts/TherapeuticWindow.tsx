import { useState, useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear, scaleBand } from '@visx/scale';
import { Bar } from '@visx/shape';
import { AxisBottom } from '@visx/axis';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface NutrientWindow {
  name: string;
  ear: number;
  rda: number;
  ul: number;
  current_intake: number;
  unit: string;
  zone: 'deficient' | 'inadequate' | 'adequate' | 'excessive';
}

interface TherapeuticWindowProps {
  data: {
    nutrients: NutrientWindow[];
  };
  title: string;
}

const ZONE_COLORS: Record<string, string> = {
  deficient: VIZ_COLORS.danger,
  inadequate: VIZ_COLORS.warning,
  adequate: VIZ_COLORS.secondary,
  excessive: VIZ_COLORS.danger,
};

const MARGIN = { top: 10, right: 30, bottom: 40, left: 120 };
const ROW_HEIGHT = 36;

const tooltipStyles = {
  ...defaultStyles,
  background: VIZ_COLORS.surface,
  color: VIZ_COLORS.text,
  border: `1px solid ${VIZ_COLORS.grid}`,
  fontFamily: 'monospace',
  fontSize: 11,
  padding: '6px 10px',
};

function TherapeuticWindowInner({
  width,
  data,
}: {
  width: number;
  data: TherapeuticWindowProps['data'];
}) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<NutrientWindow>();
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const height = MARGIN.top + MARGIN.bottom + data.nutrients.length * ROW_HEIGHT;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const maxVal = Math.max(
    ...data.nutrients.flatMap((n) => [n.ul > 0 ? n.ul * 1.1 : n.rda * 2, n.current_intake * 1.1]),
    1,
  );

  const xScale = scaleLinear<number>({
    domain: [0, maxVal],
    range: [0, innerWidth],
  });

  const yScale = scaleBand<string>({
    domain: data.nutrients.map((n) => n.name),
    range: [0, innerHeight],
    padding: 0.3,
  });

  const handleMouseOver = useCallback(
    (nutrient: NutrientWindow, left: number, top: number) => {
      showTooltip({ tooltipData: nutrient, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {data.nutrients.map((nutrient, i) => {
            const y = yScale(nutrient.name) ?? 0;
            const bh = yScale.bandwidth();
            const isHovered = hoveredIdx === i;

            const earX = xScale(nutrient.ear);
            const rdaX = xScale(nutrient.rda);
            const ulX = nutrient.ul > 0 ? xScale(nutrient.ul) : xScale(maxVal);
            const intakeX = xScale(nutrient.current_intake);

            return (
              <Group
                key={nutrient.name}
                onMouseEnter={() => {
                  setHoveredIdx(i);
                  handleMouseOver(nutrient, intakeX + MARGIN.left, y + bh / 2 + MARGIN.top);
                }}
                onMouseLeave={() => {
                  setHoveredIdx(null);
                  hideTooltip();
                }}
              >
                {/* Label */}
                <text
                  x={-8}
                  y={y + bh / 2}
                  textAnchor="end"
                  dominantBaseline="middle"
                  fill={VIZ_COLORS.text}
                  fontSize={10}
                  fontFamily="monospace"
                >
                  {nutrient.name}
                </text>

                {/* Deficient zone: 0 to EAR */}
                <Bar
                  x={0}
                  y={y}
                  width={earX}
                  height={bh}
                  fill={VIZ_COLORS.danger}
                  fillOpacity={isHovered ? 0.35 : 0.2}
                />
                {/* Inadequate zone: EAR to RDA */}
                <Bar
                  x={earX}
                  y={y}
                  width={Math.max(0, rdaX - earX)}
                  height={bh}
                  fill={VIZ_COLORS.warning}
                  fillOpacity={isHovered ? 0.35 : 0.2}
                />
                {/* Adequate zone: RDA to UL */}
                <Bar
                  x={rdaX}
                  y={y}
                  width={Math.max(0, ulX - rdaX)}
                  height={bh}
                  fill={VIZ_COLORS.secondary}
                  fillOpacity={isHovered ? 0.35 : 0.2}
                />
                {/* Excessive zone: UL onwards */}
                {nutrient.ul > 0 && (
                  <Bar
                    x={ulX}
                    y={y}
                    width={Math.max(0, xScale(maxVal) - ulX)}
                    height={bh}
                    fill={VIZ_COLORS.danger}
                    fillOpacity={isHovered ? 0.25 : 0.1}
                  />
                )}

                {/* Current intake diamond marker */}
                <polygon
                  points={`${intakeX},${y + 4} ${intakeX + 5},${y + bh / 2} ${intakeX},${y + bh - 4} ${intakeX - 5},${y + bh / 2}`}
                  fill={ZONE_COLORS[nutrient.zone]}
                  stroke={VIZ_COLORS.text}
                  strokeWidth={0.5}
                  cursor="pointer"
                />
              </Group>
            );
          })}

          <AxisBottom
            top={innerHeight}
            scale={xScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
          />
        </Group>
      </svg>
      {tooltipOpen && tooltipData && (
        <TooltipWithBounds left={tooltipLeft} top={tooltipTop} style={tooltipStyles}>
          <strong>{tooltipData.name}</strong>
          <br />
          Intake: {tooltipData.current_intake} {tooltipData.unit}
          <br />
          EAR: {tooltipData.ear} | RDA: {tooltipData.rda} | UL: {tooltipData.ul || 'N/A'}
          <br />
          Zone: <span style={{ color: ZONE_COLORS[tooltipData.zone] }}>{tooltipData.zone}</span>
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function TherapeuticWindow({ data, title }: TherapeuticWindowProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) => width > 0 && <TherapeuticWindowInner width={width} data={data} />}
      </ParentSize>
    </div>
  );
}

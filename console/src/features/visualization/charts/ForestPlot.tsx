import { useState, useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear, scaleBand } from '@visx/scale';
import { AxisBottom } from '@visx/axis';
import { Line } from '@visx/shape';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface Study {
  name: string;
  effect_size: number;
  ci_lower: number;
  ci_upper: number;
  weight: number;
}

interface ForestPlotProps {
  data: {
    studies: Study[];
    pooled: { effect_size: number; ci_lower: number; ci_upper: number };
    effect_measure: string;
  };
  title: string;
}

const MARGIN = { top: 20, right: 30, bottom: 40, left: 160 };
const ROW_HEIGHT = 28;
const POOLED_LABEL = 'Pooled estimate';

const tooltipStyles = {
  ...defaultStyles,
  background: VIZ_COLORS.surface,
  color: VIZ_COLORS.text,
  border: `1px solid ${VIZ_COLORS.grid}`,
  fontFamily: 'monospace',
  fontSize: 11,
  padding: '6px 10px',
};

function ForestPlotInner({ width, data }: { width: number; data: ForestPlotProps['data'] }) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<Study & { isPooled?: boolean }>();
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const allRows = [...data.studies, { name: POOLED_LABEL, ...data.pooled, weight: 0 }];
  const height = MARGIN.top + MARGIN.bottom + allRows.length * ROW_HEIGHT;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const allValues = data.studies.flatMap((s) => [s.ci_lower, s.ci_upper]);
  allValues.push(data.pooled.ci_lower, data.pooled.ci_upper, 0);
  const xMin = Math.min(...allValues);
  const xMax = Math.max(...allValues);
  const padding = (xMax - xMin) * 0.1;

  const xScale = scaleLinear<number>({
    domain: [xMin - padding, xMax + padding],
    range: [0, innerWidth],
  });

  const yScale = scaleBand<string>({
    domain: allRows.map((r) => r.name),
    range: [0, innerHeight],
    padding: 0.3,
  });

  const maxWeight = Math.max(...data.studies.map((s) => s.weight), 1);

  const handleMouseOver = useCallback(
    (row: Study & { isPooled?: boolean }, left: number, top: number) => {
      showTooltip({ tooltipData: row, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Null effect line */}
          <Line
            from={{ x: xScale(0), y: 0 }}
            to={{ x: xScale(0), y: innerHeight }}
            stroke={VIZ_COLORS.neutral}
            strokeDasharray="4 3"
            strokeWidth={1}
          />

          {data.studies.map((study, i) => {
            const y = (yScale(study.name) ?? 0) + (yScale.bandwidth() / 2);
            const r = 3 + (study.weight / maxWeight) * 6;
            const isHovered = hoveredIdx === i;
            return (
              <Group key={study.name}>
                {/* Study label */}
                <text
                  x={-8}
                  y={y}
                  textAnchor="end"
                  dominantBaseline="middle"
                  fill={VIZ_COLORS.text}
                  fontSize={10}
                  fontFamily="monospace"
                >
                  {study.name}
                </text>
                {/* CI line */}
                <Line
                  from={{ x: xScale(study.ci_lower), y }}
                  to={{ x: xScale(study.ci_upper), y }}
                  stroke={isHovered ? VIZ_COLORS.primary : VIZ_COLORS.neutral}
                  strokeWidth={isHovered ? 2 : 1.5}
                />
                {/* Point estimate */}
                <circle
                  cx={xScale(study.effect_size)}
                  cy={y}
                  r={r}
                  fill={VIZ_COLORS.primary}
                  fillOpacity={isHovered ? 1 : 0.8}
                  stroke={VIZ_COLORS.text}
                  strokeWidth={0.5}
                  cursor="pointer"
                  onMouseEnter={() => {
                    setHoveredIdx(i);
                    handleMouseOver(study, xScale(study.effect_size) + MARGIN.left, y + MARGIN.top);
                  }}
                  onMouseLeave={() => {
                    setHoveredIdx(null);
                    hideTooltip();
                  }}
                />
              </Group>
            );
          })}

          {/* Pooled estimate diamond */}
          {(() => {
            const y = (yScale(POOLED_LABEL) ?? 0) + (yScale.bandwidth() / 2);
            const cx = xScale(data.pooled.effect_size);
            const left = xScale(data.pooled.ci_lower);
            const right = xScale(data.pooled.ci_upper);
            const dh = 8;
            return (
              <Group>
                <text
                  x={-8}
                  y={y}
                  textAnchor="end"
                  dominantBaseline="middle"
                  fill={VIZ_COLORS.warning}
                  fontSize={10}
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {POOLED_LABEL}
                </text>
                <polygon
                  points={`${left},${y} ${cx},${y - dh} ${right},${y} ${cx},${y + dh}`}
                  fill={VIZ_COLORS.warning}
                  fillOpacity={0.8}
                  stroke={VIZ_COLORS.text}
                  strokeWidth={0.5}
                  cursor="pointer"
                  onMouseEnter={() =>
                    handleMouseOver(
                      { ...data.pooled, name: POOLED_LABEL, weight: 0, isPooled: true },
                      cx + MARGIN.left,
                      y + MARGIN.top,
                    )
                  }
                  onMouseLeave={hideTooltip}
                />
              </Group>
            );
          })()}

          <AxisBottom
            top={innerHeight}
            scale={xScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label={data.effect_measure}
            labelProps={{ fill: VIZ_COLORS.neutral, fontSize: 11, fontFamily: 'monospace' }}
          />
        </Group>
      </svg>
      {tooltipOpen && tooltipData && (
        <TooltipWithBounds left={tooltipLeft} top={tooltipTop} style={tooltipStyles}>
          <strong>{tooltipData.name}</strong>
          <br />
          Effect: {tooltipData.effect_size.toFixed(3)}
          <br />
          CI: [{tooltipData.ci_lower.toFixed(3)}, {tooltipData.ci_upper.toFixed(3)}]
          {tooltipData.weight > 0 && (
            <>
              <br />
              Weight: {tooltipData.weight.toFixed(1)}%
            </>
          )}
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function ForestPlot({ data, title }: ForestPlotProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) => width > 0 && <ForestPlotInner width={width} data={data} />}
      </ParentSize>
    </div>
  );
}

import { useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear } from '@visx/scale';
import { AxisBottom, AxisLeft } from '@visx/axis';
import { LinePath, Line } from '@visx/shape';
import { curveLinear } from '@visx/curve';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface Observation {
  x: number;
  y: number;
  side: 'left' | 'right';
}

interface FittedPoint {
  x: number;
  y: number;
}

interface RDDPlotProps {
  data: {
    observations: Observation[];
    cutoff: number;
    fitted_left: FittedPoint[];
    fitted_right: FittedPoint[];
  };
  title: string;
}

const MARGIN = { top: 20, right: 30, bottom: 50, left: 60 };

const tooltipStyles = {
  ...defaultStyles,
  background: VIZ_COLORS.surface,
  color: VIZ_COLORS.text,
  border: `1px solid ${VIZ_COLORS.grid}`,
  fontFamily: 'monospace',
  fontSize: 11,
  padding: '6px 10px',
};

function RDDPlotInner({ width, data }: { width: number; data: RDDPlotProps['data'] }) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<Observation>();

  const height = 350;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const allX = data.observations.map((p) => p.x);
  const allY = data.observations.map((p) => p.y);
  const xMin = Math.min(...allX);
  const xMax = Math.max(...allX);
  const yMin = Math.min(...allY);
  const yMax = Math.max(...allY);
  const xPad = (xMax - xMin) * 0.05 || 1;
  const yPad = (yMax - yMin) * 0.1 || 1;

  const xScale = scaleLinear<number>({
    domain: [xMin - xPad, xMax + xPad],
    range: [0, innerWidth],
  });

  const yScale = scaleLinear<number>({
    domain: [yMin - yPad, yMax + yPad],
    range: [innerHeight, 0],
  });

  const handleMouseOver = useCallback(
    (point: Observation, left: number, top: number) => {
      showTooltip({ tooltipData: point, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Fitted lines */}
          {data.fitted_left.length > 0 && (
            <LinePath
              data={data.fitted_left}
              x={(d) => xScale(d.x)}
              y={(d) => yScale(d.y)}
              curve={curveLinear}
              stroke={VIZ_COLORS.secondary}
              strokeWidth={2}
            />
          )}
          {data.fitted_right.length > 0 && (
            <LinePath
              data={data.fitted_right}
              x={(d) => xScale(d.x)}
              y={(d) => yScale(d.y)}
              curve={curveLinear}
              stroke={VIZ_COLORS.primary}
              strokeWidth={2}
            />
          )}

          {/* Cutoff line */}
          <Line
            from={{ x: xScale(data.cutoff), y: 0 }}
            to={{ x: xScale(data.cutoff), y: innerHeight }}
            stroke={VIZ_COLORS.danger}
            strokeDasharray="6 4"
            strokeWidth={1.5}
          />

          {/* Observations */}
          {data.observations.map((point, i) => (
            <circle
              key={i}
              cx={xScale(point.x)}
              cy={yScale(point.y)}
              r={3.5}
              fill={point.side === 'right' ? VIZ_COLORS.primary : VIZ_COLORS.secondary}
              fillOpacity={0.7}
              stroke={VIZ_COLORS.text}
              strokeWidth={0.3}
              cursor="pointer"
              onMouseEnter={() =>
                handleMouseOver(
                  point,
                  xScale(point.x) + MARGIN.left,
                  yScale(point.y) + MARGIN.top,
                )
              }
              onMouseLeave={hideTooltip}
            />
          ))}

          <AxisBottom
            top={innerHeight}
            scale={xScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label="Running Variable"
            labelProps={{ fill: VIZ_COLORS.neutral, fontSize: 11, fontFamily: 'monospace' }}
          />
          <AxisLeft
            scale={yScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label="Outcome"
            labelProps={{
              fill: VIZ_COLORS.neutral,
              fontSize: 11,
              fontFamily: 'monospace',
              textAnchor: 'middle',
            }}
          />
        </Group>
      </svg>
      {tooltipOpen && tooltipData && (
        <TooltipWithBounds left={tooltipLeft} top={tooltipTop} style={tooltipStyles}>
          X: {tooltipData.x.toFixed(2)}
          <br />
          Y: {tooltipData.y.toFixed(3)}
          <br />
          Side: {tooltipData.side}
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function RDDPlot({ data, title }: RDDPlotProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) => width > 0 && <RDDPlotInner width={width} data={data} />}
      </ParentSize>
    </div>
  );
}

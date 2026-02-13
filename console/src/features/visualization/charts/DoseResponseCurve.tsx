import { useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear } from '@visx/scale';
import { AxisBottom, AxisLeft } from '@visx/axis';
import { LinePath, AreaClosed, Line } from '@visx/shape';
import { curveNatural } from '@visx/curve';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface DataPoint {
  dose: number;
  effect: number;
  ci_lower: number;
  ci_upper: number;
}

interface DoseResponseCurveProps {
  data: {
    points: DataPoint[];
    dose_label: string;
    effect_label: string;
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

function DoseResponseInner({ width, data }: { width: number; data: DoseResponseCurveProps['data'] }) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<DataPoint>();

  const height = 350;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const doseMin = Math.min(...data.points.map((p) => p.dose));
  const doseMax = Math.max(...data.points.map((p) => p.dose));
  const dosePad = (doseMax - doseMin) * 0.05 || 1;

  const allEffects = data.points.flatMap((p) => [p.effect, p.ci_lower, p.ci_upper]);
  const effectMin = Math.min(...allEffects);
  const effectMax = Math.max(...allEffects);
  const effectPad = (effectMax - effectMin) * 0.1 || 0.1;

  const xScale = scaleLinear<number>({
    domain: [doseMin - dosePad, doseMax + dosePad],
    range: [0, innerWidth],
  });

  const yScale = scaleLinear<number>({
    domain: [effectMin - effectPad, effectMax + effectPad],
    range: [innerHeight, 0],
  });

  const showNullLine = effectMin < 0 && effectMax > 0;

  const handleMouseOver = useCallback(
    (point: DataPoint, left: number, top: number) => {
      showTooltip({ tooltipData: point, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Confidence band */}
          <AreaClosed
            data={data.points}
            x={(d) => xScale(d.dose)}
            y0={(d) => yScale(d.ci_lower)}
            y1={(d) => yScale(d.ci_upper)}
            yScale={yScale}
            curve={curveNatural}
            fill={VIZ_COLORS.primary}
            fillOpacity={0.15}
          />

          {/* Main curve */}
          <LinePath
            data={data.points}
            x={(d) => xScale(d.dose)}
            y={(d) => yScale(d.effect)}
            curve={curveNatural}
            stroke={VIZ_COLORS.primary}
            strokeWidth={2.5}
          />

          {/* Null effect line */}
          {showNullLine && (
            <Line
              from={{ x: 0, y: yScale(0) }}
              to={{ x: innerWidth, y: yScale(0) }}
              stroke={VIZ_COLORS.neutral}
              strokeDasharray="4 3"
              strokeWidth={1}
            />
          )}

          {/* Data points */}
          {data.points.map((point, i) => (
            <circle
              key={i}
              cx={xScale(point.dose)}
              cy={yScale(point.effect)}
              r={4}
              fill={VIZ_COLORS.primary}
              stroke={VIZ_COLORS.text}
              strokeWidth={0.5}
              cursor="pointer"
              onMouseEnter={() =>
                handleMouseOver(
                  point,
                  xScale(point.dose) + MARGIN.left,
                  yScale(point.effect) + MARGIN.top,
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
            label={data.dose_label}
            labelProps={{ fill: VIZ_COLORS.neutral, fontSize: 11, fontFamily: 'monospace' }}
          />
          <AxisLeft
            scale={yScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label={data.effect_label}
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
          {data.dose_label}: {tooltipData.dose.toFixed(1)}
          <br />
          {data.effect_label}: {tooltipData.effect.toFixed(3)}
          <br />
          CI: [{tooltipData.ci_lower.toFixed(3)}, {tooltipData.ci_upper.toFixed(3)}]
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function DoseResponseCurve({ data, title }: DoseResponseCurveProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) => width > 0 && <DoseResponseInner width={width} data={data} />}
      </ParentSize>
    </div>
  );
}

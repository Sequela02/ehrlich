import { useState, useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear } from '@visx/scale';
import { AxisBottom, AxisLeft } from '@visx/axis';
import { Line, LinePath } from '@visx/shape';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface Study {
  name: string;
  effect_size: number;
  se: number;
  precision: number;
  sample_size: number;
}

interface FunnelPlotProps {
  data: {
    studies: Study[];
    pooled_effect: number;
    funnel_bounds: Array<{ precision: number; ci_lower: number; ci_upper: number }>;
    effect_measure: string;
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

function FunnelPlotInner({ width, data }: { width: number; data: FunnelPlotProps['data'] }) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<Study>();
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const height = 350;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const allEffects = data.studies.map((s) => s.effect_size);
  const allBoundsLower = data.funnel_bounds.map((b) => b.ci_lower);
  const allBoundsUpper = data.funnel_bounds.map((b) => b.ci_upper);
  const effectMin = Math.min(...allEffects, ...allBoundsLower, data.pooled_effect);
  const effectMax = Math.max(...allEffects, ...allBoundsUpper, data.pooled_effect);
  const effectPad = (effectMax - effectMin) * 0.15 || 0.5;

  const maxPrecision = Math.max(...data.studies.map((s) => s.precision), 1);
  const maxSampleSize = Math.max(...data.studies.map((s) => s.sample_size), 1);

  const xScale = scaleLinear<number>({
    domain: [effectMin - effectPad, effectMax + effectPad],
    range: [0, innerWidth],
  });

  const yScale = scaleLinear<number>({
    domain: [0, maxPrecision * 1.1],
    range: [innerHeight, 0],
  });

  const handleMouseOver = useCallback(
    (study: Study, left: number, top: number) => {
      showTooltip({ tooltipData: study, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Funnel boundary lines */}
          <LinePath
            data={data.funnel_bounds}
            x={(d) => xScale(d.ci_lower)}
            y={(d) => yScale(d.precision)}
            stroke={VIZ_COLORS.neutral}
            strokeDasharray="4 3"
            strokeWidth={1}
          />
          <LinePath
            data={data.funnel_bounds}
            x={(d) => xScale(d.ci_upper)}
            y={(d) => yScale(d.precision)}
            stroke={VIZ_COLORS.neutral}
            strokeDasharray="4 3"
            strokeWidth={1}
          />

          {/* Pooled effect vertical line */}
          <Line
            from={{ x: xScale(data.pooled_effect), y: 0 }}
            to={{ x: xScale(data.pooled_effect), y: innerHeight }}
            stroke={VIZ_COLORS.warning}
            strokeDasharray="6 3"
            strokeWidth={1.5}
          />

          {/* Study points */}
          {data.studies.map((study, i) => {
            const r = 3 + (study.sample_size / maxSampleSize) * 5;
            const isHovered = hoveredIdx === i;
            return (
              <circle
                key={study.name}
                cx={xScale(study.effect_size)}
                cy={yScale(study.precision)}
                r={r}
                fill={VIZ_COLORS.primary}
                fillOpacity={isHovered ? 1 : 0.7}
                stroke={VIZ_COLORS.text}
                strokeWidth={0.5}
                cursor="pointer"
                onMouseEnter={() => {
                  setHoveredIdx(i);
                  handleMouseOver(
                    study,
                    xScale(study.effect_size) + MARGIN.left,
                    yScale(study.precision) + MARGIN.top,
                  );
                }}
                onMouseLeave={() => {
                  setHoveredIdx(null);
                  hideTooltip();
                }}
              />
            );
          })}

          <AxisBottom
            top={innerHeight}
            scale={xScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label={data.effect_measure}
            labelProps={{ fill: VIZ_COLORS.neutral, fontSize: 11, fontFamily: 'monospace' }}
          />
          <AxisLeft
            scale={yScale}
            stroke={VIZ_COLORS.grid}
            tickStroke={VIZ_COLORS.grid}
            tickLabelProps={{ fill: VIZ_COLORS.neutral, fontSize: 10, fontFamily: 'monospace' }}
            label="Precision (1/SE)"
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
          <strong>{tooltipData.name}</strong>
          <br />
          Effect: {tooltipData.effect_size.toFixed(3)}
          <br />
          SE: {tooltipData.se.toFixed(3)}
          {tooltipData.sample_size > 0 && (
            <>
              <br />
              N: {tooltipData.sample_size}
            </>
          )}
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function FunnelPlot({ data, title }: FunnelPlotProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) => width > 0 && <FunnelPlotInner width={width} data={data} />}
      </ParentSize>
    </div>
  );
}

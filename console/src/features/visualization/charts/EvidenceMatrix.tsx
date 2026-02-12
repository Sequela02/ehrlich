import { useState, useCallback } from 'react';
import { Group } from '@visx/group';
import { scaleLinear, scaleBand } from '@visx/scale';
import { HeatmapRect } from '@visx/heatmap';
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip';
import { ParentSize } from '@visx/responsive';
import { VIZ_COLORS } from '../theme';

interface EvidenceMatrixProps {
  data: {
    rows: string[];
    cols: string[];
    values: number[][];
  };
  title: string;
  onCellClick?: (row: number, col: number) => void;
}

const MARGIN = { top: 80, right: 20, bottom: 20, left: 140 };
const CELL_SIZE = 36;

const tooltipStyles = {
  ...defaultStyles,
  background: VIZ_COLORS.surface,
  color: VIZ_COLORS.text,
  border: `1px solid ${VIZ_COLORS.grid}`,
  fontFamily: 'monospace',
  fontSize: 11,
  padding: '6px 10px',
};

function divergingColor(v: number): string {
  if (v > 0) {
    const t = Math.min(v, 1);
    return `oklch(${0.55 + 0.1 * (1 - t)} ${0.15 * t} 160)`;
  }
  if (v < 0) {
    const t = Math.min(-v, 1);
    return `oklch(${0.55 + 0.08 * (1 - t)} ${0.22 * t} 25)`;
  }
  return VIZ_COLORS.neutral;
}

interface CellInfo {
  row: string;
  col: string;
  value: number;
  rowIdx: number;
  colIdx: number;
}

function EvidenceMatrixInner({
  width: parentWidth,
  data,
  onCellClick,
}: {
  width: number;
  data: EvidenceMatrixProps['data'];
  onCellClick?: (row: number, col: number) => void;
}) {
  const { showTooltip, hideTooltip, tooltipData, tooltipLeft, tooltipTop, tooltipOpen } =
    useTooltip<CellInfo>();
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);

  const numCols = data.cols.length;
  const numRows = data.rows.length;
  const width = Math.min(parentWidth, MARGIN.left + MARGIN.right + numCols * CELL_SIZE);
  const height = MARGIN.top + MARGIN.bottom + numRows * CELL_SIZE;
  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  const xScale = scaleBand<string>({
    domain: data.cols,
    range: [0, innerWidth],
    padding: 0.05,
  });

  const yScale = scaleBand<string>({
    domain: data.rows,
    range: [0, innerHeight],
    padding: 0.05,
  });

  const colorScale = scaleLinear<string>({
    domain: [-1, 0, 1],
    range: [VIZ_COLORS.danger, VIZ_COLORS.neutral, VIZ_COLORS.secondary],
  });

  // Transform data for HeatmapRect
  const bins = data.cols.map((_col, ci) => ({
    bin: ci,
    bins: data.rows.map((_row, ri) => ({
      bin: ri,
      count: data.values[ri]?.[ci] ?? 0,
    })),
  }));

  const handleMouseOver = useCallback(
    (info: CellInfo, left: number, top: number) => {
      showTooltip({ tooltipData: info, tooltipLeft: left, tooltipTop: top });
    },
    [showTooltip],
  );

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group left={MARGIN.left} top={MARGIN.top}>
          {/* Column labels (rotated) */}
          {data.cols.map((col, _ci) => (
            <text
              key={col}
              x={(xScale(col) ?? 0) + xScale.bandwidth() / 2}
              y={-8}
              textAnchor="start"
              transform={`rotate(-45, ${(xScale(col) ?? 0) + xScale.bandwidth() / 2}, -8)`}
              fill={VIZ_COLORS.text}
              fontSize={10}
              fontFamily="monospace"
            >
              {col.length > 18 ? col.slice(0, 16) + '..' : col}
            </text>
          ))}

          {/* Row labels */}
          {data.rows.map((row) => (
            <text
              key={row}
              x={-8}
              y={(yScale(row) ?? 0) + yScale.bandwidth() / 2}
              textAnchor="end"
              dominantBaseline="middle"
              fill={VIZ_COLORS.text}
              fontSize={10}
              fontFamily="monospace"
            >
              {row.length > 20 ? row.slice(0, 18) + '..' : row}
            </text>
          ))}

          {/* Heatmap cells */}
          <HeatmapRect
            data={bins}
            xScale={(d) => xScale(data.cols[d as number]) ?? 0}
            yScale={(d) => yScale(data.rows[d as number]) ?? 0}
            colorScale={colorScale}
            binWidth={xScale.bandwidth()}
            binHeight={yScale.bandwidth()}
          >
            {(heatmap) =>
              heatmap.map((columnBins) =>
                columnBins.map((bin) => {
                  const ci = bin.column;
                  const ri = bin.row;
                  const key = `${ri}-${ci}`;
                  const isHovered = hoveredCell === key;
                  const value = data.values[ri]?.[ci] ?? 0;
                  return (
                    <rect
                      key={key}
                      x={bin.x}
                      y={bin.y}
                      width={bin.width}
                      height={bin.height}
                      fill={divergingColor(value)}
                      fillOpacity={isHovered ? 1 : 0.85}
                      stroke={isHovered ? VIZ_COLORS.text : VIZ_COLORS.grid}
                      strokeWidth={isHovered ? 1.5 : 0.5}
                      rx={2}
                      cursor={onCellClick ? 'pointer' : 'default'}
                      onMouseEnter={() => {
                        setHoveredCell(key);
                        handleMouseOver(
                          { row: data.rows[ri], col: data.cols[ci], value, rowIdx: ri, colIdx: ci },
                          bin.x + MARGIN.left + bin.width / 2,
                          bin.y + MARGIN.top,
                        );
                      }}
                      onMouseLeave={() => {
                        setHoveredCell(null);
                        hideTooltip();
                      }}
                      onClick={() => onCellClick?.(ri, ci)}
                    />
                  );
                }),
              )
            }
          </HeatmapRect>
        </Group>
      </svg>
      {tooltipOpen && tooltipData && (
        <TooltipWithBounds left={tooltipLeft} top={tooltipTop} style={tooltipStyles}>
          <strong>{tooltipData.row}</strong>
          <br />
          Source: {tooltipData.col}
          <br />
          Value: {tooltipData.value.toFixed(2)}
          <br />
          {tooltipData.value > 0 ? 'Supporting' : tooltipData.value < 0 ? 'Contradicting' : 'Neutral'}
        </TooltipWithBounds>
      )}
    </div>
  );
}

export default function EvidenceMatrix({ data, title, onCellClick }: EvidenceMatrixProps) {
  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <ParentSize debounceTime={100}>
        {({ width }) =>
          width > 0 && <EvidenceMatrixInner width={width} data={data} onCellClick={onCellClick} />
        }
      </ParentSize>
    </div>
  );
}

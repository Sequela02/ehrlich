import { useCallback, useMemo, useRef, useState } from 'react';
import {
  BACK_PATHS,
  BODY_OUTLINE_BACK,
  BODY_OUTLINE_FRONT,
  FRONT_PATHS,
  MUSCLE_ALIASES,
  MUSCLE_LABELS,
} from './body-paths';
import { getIntensityColor } from './color-scale';

export interface MuscleData {
  muscle: string;
  intensity: number;
  label?: string;
}

export interface BodyDiagramProps {
  data: {
    muscles: MuscleData[];
    view: 'front' | 'back';
  };
  title: string;
  mode?: 'activation' | 'risk';
  onMuscleClick?: (muscle: string) => void;
}

interface TooltipState {
  x: number;
  y: number;
  name: string;
  intensity: number;
  label?: string;
}

type MuscleMap = Map<string, { intensity: number; label?: string; source: string }>;

function buildMuscleMap(muscles: MuscleData[]): MuscleMap {
  const map: MuscleMap = new Map();
  for (const m of muscles) {
    const keys = MUSCLE_ALIASES[m.muscle.toLowerCase()] ?? [m.muscle.replace(/-/g, '_')];
    for (const key of keys) {
      map.set(key, { intensity: m.intensity, label: m.label, source: m.muscle });
    }
  }
  return map;
}

export default function BodyDiagram({
  data,
  title,
  mode = 'activation',
  onMuscleClick,
}: BodyDiagramProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const paths = data.view === 'front' ? FRONT_PATHS : BACK_PATHS;
  const outline = data.view === 'front' ? BODY_OUTLINE_FRONT : BODY_OUTLINE_BACK;

  const muscleMap = useMemo(() => buildMuscleMap(data.muscles), [data.muscles]);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent, pathKey: string) => {
      const entry = muscleMap.get(pathKey);
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return;
      setTooltip({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top - 10,
        name: MUSCLE_LABELS[pathKey] ?? pathKey,
        intensity: entry?.intensity ?? 0,
        label: entry?.label,
      });
    },
    [muscleMap],
  );

  const handleMouseLeave = useCallback(() => setTooltip(null), []);

  const handleClick = useCallback(
    (pathKey: string) => {
      setSelected(pathKey === selected ? null : pathKey);
      const entry = muscleMap.get(pathKey);
      onMuscleClick?.(entry?.source ?? pathKey);
    },
    [selected, muscleMap, onMuscleClick],
  );

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: 320 }}>
      <h3
        style={{
          textAlign: 'center',
          margin: '0 0 8px',
          fontSize: 14,
          fontWeight: 600,
          color: 'oklch(0.85 0.02 250)',
        }}
      >
        {title}
        <span
          style={{
            marginLeft: 8,
            fontSize: 11,
            fontWeight: 400,
            color: 'oklch(0.6 0.02 250)',
            textTransform: 'capitalize',
          }}
        >
          ({data.view} view)
        </span>
      </h3>

      <svg
        ref={svgRef}
        viewBox="0 0 200 400"
        width="100%"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`${title} - ${data.view} view body diagram`}
        style={{ display: 'block' }}
      >
        {/* Body outline */}
        <path
          d={outline}
          fill="none"
          stroke="oklch(0.5 0.02 250)"
          strokeWidth={0.8}
          strokeLinejoin="round"
        />

        {/* Muscle regions */}
        {Object.entries(paths).map(([key, d]) => {
          const entry = muscleMap.get(key);
          const hasData = entry !== undefined;
          const intensity = entry?.intensity ?? 0;
          const isSelected = selected === key;
          const fill = hasData
            ? getIntensityColor(intensity, mode)
            : 'oklch(0.3 0.01 250)';

          return (
            <path
              key={key}
              d={d}
              fill={fill}
              fillOpacity={hasData ? 0.85 : 0.1}
              stroke={
                isSelected
                  ? 'oklch(0.95 0.01 250)'
                  : hasData
                    ? 'oklch(0.35 0.03 250)'
                    : 'oklch(0.3 0.01 250)'
              }
              strokeWidth={isSelected ? 2 : 0.6}
              strokeLinejoin="round"
              role="button"
              aria-label={MUSCLE_LABELS[key] ?? key}
              tabIndex={0}
              style={{ cursor: 'pointer', transition: 'fill 0.2s, stroke-width 0.15s' }}
              onMouseMove={(e) => handleMouseMove(e, key)}
              onMouseLeave={handleMouseLeave}
              onClick={() => handleClick(key)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleClick(key);
                }
              }}
            />
          );
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x,
            top: tooltip.y,
            transform: 'translate(-50%, -100%)',
            background: 'oklch(0.2 0.02 250)',
            border: '1px solid oklch(0.35 0.03 250)',
            borderRadius: 6,
            padding: '6px 10px',
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
            zIndex: 10,
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'oklch(0.9 0.02 250)',
            }}
          >
            {tooltip.name}
          </div>
          <div
            style={{
              fontSize: 11,
              color: getIntensityColor(tooltip.intensity, mode),
              marginTop: 2,
            }}
          >
            {Math.round(tooltip.intensity * 100)}%
            {tooltip.label && (
              <span style={{ color: 'oklch(0.65 0.02 250)', marginLeft: 6 }}>
                {tooltip.label}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          marginTop: 8,
          fontSize: 10,
          color: 'oklch(0.6 0.02 250)',
        }}
      >
        <span>{mode === 'risk' ? 'Low' : 'Inactive'}</span>
        <div
          style={{
            width: 100,
            height: 8,
            borderRadius: 4,
            background: `linear-gradient(to right, ${getIntensityColor(0, mode)}, ${getIntensityColor(0.5, mode)}, ${getIntensityColor(1, mode)})`,
          }}
        />
        <span>{mode === 'risk' ? 'High' : 'Max'}</span>
      </div>
    </div>
  );
}

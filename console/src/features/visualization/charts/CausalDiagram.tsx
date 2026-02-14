import { VIZ_COLORS } from '../theme';

interface CausalNode {
  id: string;
  label: string;
  type: 'treatment' | 'outcome' | 'confounder' | 'mediator' | 'instrument';
}

interface CausalEdge {
  source: string;
  target: string;
  type: 'causal' | 'association' | 'instrument';
}

interface CausalDiagramProps {
  data: {
    nodes: CausalNode[];
    edges: CausalEdge[];
  };
  title: string;
}

const NODE_COLORS: Record<string, string> = {
  treatment: VIZ_COLORS.primary,
  outcome: VIZ_COLORS.secondary,
  confounder: VIZ_COLORS.warning,
  mediator: VIZ_COLORS.neutral,
  instrument: VIZ_COLORS.danger,
};

const NODE_WIDTH = 120;
const NODE_HEIGHT = 40;
const SVG_WIDTH = 600;
const SVG_HEIGHT = 400;

function layoutNodes(nodes: CausalNode[]) {
  // Simple layout: treatment left, outcome right, confounders top, mediators middle
  const positions: Record<string, { x: number; y: number }> = {};
  const treatments = nodes.filter((n) => n.type === 'treatment');
  const outcomes = nodes.filter((n) => n.type === 'outcome');
  const confounders = nodes.filter((n) => n.type === 'confounder');
  const mediators = nodes.filter((n) => n.type === 'mediator');
  const instruments = nodes.filter((n) => n.type === 'instrument');

  // Place treatments on the left
  treatments.forEach((n, i) => {
    positions[n.id] = { x: 80, y: 180 + i * 80 };
  });

  // Place outcomes on the right
  outcomes.forEach((n, i) => {
    positions[n.id] = { x: SVG_WIDTH - 80 - NODE_WIDTH, y: 180 + i * 80 };
  });

  // Place confounders on top
  const confStart = (SVG_WIDTH - confounders.length * 140) / 2;
  confounders.forEach((n, i) => {
    positions[n.id] = { x: confStart + i * 140, y: 40 };
  });

  // Place mediators in the middle
  mediators.forEach((n, i) => {
    positions[n.id] = { x: SVG_WIDTH / 2 - NODE_WIDTH / 2, y: 180 + i * 80 };
  });

  // Place instruments to the far left
  instruments.forEach((n, i) => {
    positions[n.id] = { x: 10, y: 100 + i * 80 };
  });

  return positions;
}

function Arrow({ x1, y1, x2, y2, dashed, color }: {
  x1: number; y1: number; x2: number; y2: number; dashed: boolean; color: string;
}) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 1) return null;

  // Shorten to not overlap with node
  const shorten = 20;
  const ratio1 = shorten / len;
  const ratio2 = (len - shorten) / len;
  const sx = x1 + dx * ratio1;
  const sy = y1 + dy * ratio1;
  const ex = x1 + dx * ratio2;
  const ey = y1 + dy * ratio2;

  // Arrowhead
  const headLen = 8;
  const angle = Math.atan2(ey - sy, ex - sx);
  const ax1 = ex - headLen * Math.cos(angle - Math.PI / 6);
  const ay1 = ey - headLen * Math.sin(angle - Math.PI / 6);
  const ax2 = ex - headLen * Math.cos(angle + Math.PI / 6);
  const ay2 = ey - headLen * Math.sin(angle + Math.PI / 6);

  return (
    <g>
      <line
        x1={sx} y1={sy} x2={ex} y2={ey}
        stroke={color}
        strokeWidth={1.5}
        strokeDasharray={dashed ? '6 4' : undefined}
      />
      <polygon
        points={`${ex},${ey} ${ax1},${ay1} ${ax2},${ay2}`}
        fill={color}
      />
    </g>
  );
}

export default function CausalDiagram({ data, title }: CausalDiagramProps) {
  const positions = layoutNodes(data.nodes);

  return (
    <div>
      <h4
        className="mb-3 font-mono text-xs font-medium uppercase tracking-wider"
        style={{ color: VIZ_COLORS.text }}
      >
        {title}
      </h4>
      <svg width="100%" viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}>
        <rect width={SVG_WIDTH} height={SVG_HEIGHT} fill="transparent" />

        {/* Edges */}
        {data.edges.map((edge, i) => {
          const src = positions[edge.source];
          const tgt = positions[edge.target];
          if (!src || !tgt) return null;
          const color = edge.type === 'association' ? VIZ_COLORS.warning : VIZ_COLORS.text;
          return (
            <Arrow
              key={i}
              x1={src.x + NODE_WIDTH / 2}
              y1={src.y + NODE_HEIGHT / 2}
              x2={tgt.x + NODE_WIDTH / 2}
              y2={tgt.y + NODE_HEIGHT / 2}
              dashed={edge.type === 'association'}
              color={color}
            />
          );
        })}

        {/* Nodes */}
        {data.nodes.map((node) => {
          const pos = positions[node.id];
          if (!pos) return null;
          const color = NODE_COLORS[node.type] || VIZ_COLORS.neutral;
          const isRound = node.type === 'confounder' || node.type === 'instrument';

          return (
            <g key={node.id}>
              {isRound ? (
                <ellipse
                  cx={pos.x + NODE_WIDTH / 2}
                  cy={pos.y + NODE_HEIGHT / 2}
                  rx={NODE_WIDTH / 2}
                  ry={NODE_HEIGHT / 2}
                  fill={VIZ_COLORS.surface}
                  stroke={color}
                  strokeWidth={2}
                />
              ) : (
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={NODE_WIDTH}
                  height={NODE_HEIGHT}
                  rx={4}
                  fill={VIZ_COLORS.surface}
                  stroke={color}
                  strokeWidth={2}
                />
              )}
              <text
                x={pos.x + NODE_WIDTH / 2}
                y={pos.y + NODE_HEIGHT / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fill={VIZ_COLORS.text}
                fontFamily="monospace"
                fontSize={11}
              >
                {node.label.length > 14 ? node.label.slice(0, 14) + '...' : node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-3 font-mono text-[10px]" style={{ color: VIZ_COLORS.neutral }}>
        <span><span style={{ color: VIZ_COLORS.primary }}>--</span> Treatment</span>
        <span><span style={{ color: VIZ_COLORS.secondary }}>--</span> Outcome</span>
        <span><span style={{ color: VIZ_COLORS.warning }}>--</span> Confounder</span>
        <span>-- Causal &nbsp; - - Association</span>
      </div>
    </div>
  );
}

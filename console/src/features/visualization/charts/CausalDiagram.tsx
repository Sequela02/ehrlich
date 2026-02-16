import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Edge,
  Node,
  Position,
  Handle,
  NodeProps,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { VIZ_COLORS } from '../theme';

// -- [Types] -------------------------------------------------------------

interface CausalNode extends Record<string, unknown> {
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

// -- [Constants] ---------------------------------------------------------

const NODE_COLORS: Record<string, string> = {
  treatment: VIZ_COLORS.primary,
  outcome: VIZ_COLORS.secondary,
  confounder: VIZ_COLORS.warning,
  mediator: VIZ_COLORS.neutral,
  instrument: VIZ_COLORS.danger,
};

const NODE_WIDTH = 150;
const NODE_HEIGHT = 50;
const X_SPACING = 250;
const Y_SPACING = 80;

// -- [Custom Node] -------------------------------------------------------

function CausalNodeComponent({ data }: NodeProps<Node<CausalNode>>) {
  const color = NODE_COLORS[data.type] || VIZ_COLORS.neutral;
  const isRound = data.type === 'confounder' || data.type === 'instrument';

  return (
    <div
      className="flex items-center justify-center p-2 text-center transition-shadow hover:shadow-lg"
      style={{
        width: NODE_WIDTH,
        minHeight: NODE_HEIGHT,
        backgroundColor: VIZ_COLORS.surface,
        border: `2px solid ${color}`,
        borderRadius: isRound ? '24px' : '6px', // Rounded for confounders
        color: VIZ_COLORS.text,
        fontSize: '11px',
        fontFamily: 'ui-monospace, monospace',
        lineHeight: 1.2,
      }}
      title={data.label} // Native tooltip for full text
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <span className="line-clamp-3">{data.label}</span>
      <Handle type="source" position={Position.Right} className="!opacity-0" />

      {/* Add Top/Bottom handles for Confounders which might connect vertically */}
      <Handle type="target" id="top" position={Position.Top} className="!opacity-0" />
      <Handle type="source" id="bottom" position={Position.Bottom} className="!opacity-0" />
    </div>
  );
}

const nodeTypes = {
  causal: CausalNodeComponent,
};

// -- [Layout Logic] ------------------------------------------------------

function getLayoutedElements(nodes: CausalNode[], edges: CausalEdge[]) {
  // Group nodes by type
  const treatments = nodes.filter((n) => n.type === 'treatment');
  const outcomes = nodes.filter((n) => n.type === 'outcome');
  const confounders = nodes.filter((n) => n.type === 'confounder');
  const mediators = nodes.filter((n) => n.type === 'mediator');
  const instruments = nodes.filter((n) => n.type === 'instrument');

  const rfNodes: Node<CausalNode>[] = [];
  const rfEdges: Edge[] = [];

  // Helper to place a column of nodes
  const placeColumn = (group: CausalNode[], x: number) => {
    // Center the group vertically around Y=200 (approx canvas center)
    const totalHeight = group.length * Y_SPACING;
    let currentY = 200 - totalHeight / 2;

    group.forEach((node) => {
      rfNodes.push({
        id: node.id,
        type: 'causal',
        position: { x, y: currentY },
        data: node,
      });
      currentY += Y_SPACING;
    });
  };

  // 1. Instruments (Far Left)
  placeColumn(instruments, 0);

  // 2. Treatments (Left)
  placeColumn(treatments, X_SPACING);

  // 3. Mediators (Middle)
  placeColumn(mediators, X_SPACING * 2);

  // 4. Outcomes (Right)
  placeColumn(outcomes, X_SPACING * 3);

  // 5. Confounders (Top Center)
  if (confounders.length > 0) {
    // Place them in a row above everything
    confounders.forEach((node, i) => {
      rfNodes.push({
        id: node.id,
        type: 'causal',
        position: {
          // Spread around center 500 (approx between treatment and outcome)
          x: 500 + (i - (confounders.length - 1) / 2) * (NODE_WIDTH + 40),
          y: -150
        },
        data: node,
      });
    });
  }

  // Edges
  edges.forEach((edge, i) => {
    const isAssociation = edge.type === 'association';
    rfEdges.push({
      id: `e-${i}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep', // Orthogonal routing is cleaner for diagrams
      animated: isAssociation,
      style: {
        stroke: isAssociation ? VIZ_COLORS.warning : VIZ_COLORS.text,
        strokeDasharray: isAssociation ? '5 5' : undefined,
        strokeWidth: 1.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isAssociation ? VIZ_COLORS.warning : VIZ_COLORS.text,
      },
    });
  });

  return { rfNodes, rfEdges };
}

// -- [Component] ---------------------------------------------------------

export default function CausalDiagram({ data, title }: CausalDiagramProps) {
  const { rfNodes, rfEdges } = useMemo(() => getLayoutedElements(data.nodes, data.edges), [data]);

  const [nodes, , onNodesChange] = useNodesState(rfNodes);
  const [edges, , onEdgesChange] = useEdgesState(rfEdges);

  return (
    <div className="flex flex-col h-[500px] w-full border border-border rounded-md bg-background overflow-hidden relative">
      <div className="absolute top-3 left-3 z-10 bg-background/80 backdrop-blur px-2 py-1 rounded border border-border">
        <h4 className="font-mono text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {title}
        </h4>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        edgesFocusable={false}
        nodesConnectable={false}
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
        className="bg-zinc-950"
      >
        <Background color={VIZ_COLORS.grid || "#333"} gap={20} size={1} />
        <Controls showInteractive={false} position="bottom-right" />
        <MiniMap
          nodeColor={(n) => {
            const type = n.data?.type as string;
            return NODE_COLORS[type] || VIZ_COLORS.neutral;
          }}
          maskColor="rgba(0,0,0,0.6)"
          position="bottom-left"
        />

        {/* Legend */}
        <div className="absolute bottom-2 left-20 right-20 flex justify-center pointer-events-none">
          <div className="flex gap-4 px-3 py-1.5 bg-background/90 backdrop-blur border border-border rounded-full shadow-sm">
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-[10px] uppercase font-mono text-muted-foreground">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </ReactFlow>
    </div>
  );
}

import { ReactFlow, Background, Controls, MiniMap, Panel } from "@xyflow/react";
import type { Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { BrainCircuit, FlaskConical, FileText, Wrench } from "lucide-react";
import type { InvestigationNodeData } from "../lib/diagram-builder";
import { InvestigationNode } from "./InvestigationNode";

// -- Custom node types ----------------------------------------------------

function AnnotationNode({ data }: { data: InvestigationNodeData }) {
  return (
    <span
      style={{
        color: data.textColor,
        fontSize: 13,
        fontFamily: "ui-monospace, monospace",
        fontWeight: 500,
        letterSpacing: "0.05em",
      }}
    >
      {data.label}
    </span>
  );
}

const nodeTypes = {
  investigation: InvestigationNode,
  annotation: AnnotationNode,
};

// -- Legend Component -----------------------------------------------------

const LEGEND_ITEMS = [
  { label: "Hypothesis", icon: BrainCircuit, color: "var(--color-primary)" },
  { label: "Experiment", icon: FlaskConical, color: "#22c55e" },
  { label: "Finding", icon: FileText, color: "#6b7280" },
  { label: "Tool Execution", icon: Wrench, color: "var(--color-muted-foreground)" },
];

function Legend() {
  return (
    <div className="bg-popover/90 backdrop-blur border border-border rounded-md p-3 shadow-lg space-y-2 max-w-[200px]">
      <h4 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-2 border-b border-border pb-1">Legend</h4>
      <div className="space-y-1.5">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2 text-xs">
            <item.icon className="w-3.5 h-3.5" style={{ color: item.color }} />
            <span className="text-foreground/90">{item.label}</span>
          </div>
        ))}
      </div>
      <div className="text-[10px] text-muted-foreground pt-2 border-t border-border/50 italic leading-snug">
        Hover over nodes to see detailed scientific reasoning.
      </div>
    </div>
  );
}

// -- Diagram renderer component -------------------------------------------

interface DiagramRendererProps {
  nodes: Node<InvestigationNodeData>[];
  edges: Edge[];
}

export function DiagramRenderer({ nodes, edges }: DiagramRendererProps) {
  if (nodes.length === 0) return null;

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      proOptions={{ hideAttribution: true }}
      colorMode="dark" // Enforce dark mode or use system preference? Debug used forced styles mostly.
      minZoom={0.1}
      maxZoom={2}
      className="bg-zinc-50 dark:bg-zinc-900"
    >
      <Background color="var(--color-border)" gap={32} size={1} />
      <Controls
        position="top-left"
        showInteractive={false}
        className="!bg-card !border-border !shadow-sm [&>button]:!bg-card [&>button]:!border-border [&>button]:!fill-foreground [&>button:hover]:!bg-muted"
      />
      <MiniMap
        nodeColor={(n) => (n.data as InvestigationNodeData).fill ?? "#1f2937"}
        maskColor="rgba(15, 18, 25, 0.8)"
        style={{ backgroundColor: "#0f1219" }}
      />
      <Panel position="bottom-left">
        <Legend />
      </Panel>
    </ReactFlow>
  );
}

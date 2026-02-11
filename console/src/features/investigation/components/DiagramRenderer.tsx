import { ReactFlow, Background, Controls, MiniMap, Handle, Position } from "@xyflow/react";
import type { NodeProps, Node, Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { InvestigationNodeData } from "../lib/diagram-builder";

// -- Custom node types (defined outside component to avoid re-registration) --

function InvestigationNode({ data }: NodeProps<Node<InvestigationNodeData>>) {
  return (
    <div
      style={{
        width: 260,
        height: 80,
        borderRadius: 8,
        border: `2px solid ${data.stroke}`,
        backgroundColor: data.fill,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "8px 12px",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <span
        style={{
          color: data.textColor,
          fontSize: 13,
          fontFamily: "system-ui, sans-serif",
          textAlign: "center",
          lineHeight: 1.3,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          maxWidth: "100%",
        }}
      >
        {data.label}
      </span>
      <span
        style={{
          color: data.textColor,
          fontSize: 11,
          fontFamily: "ui-monospace, monospace",
          opacity: 0.7,
          marginTop: 4,
        }}
      >
        {data.sublabel}
      </span>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

function AnnotationNode({ data }: NodeProps<Node<InvestigationNodeData>>) {
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
      colorMode="dark"
      minZoom={0.3}
      maxZoom={2}
    >
      <Background color="#1f2937" gap={20} />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(n) => (n.data as InvestigationNodeData).fill ?? "#1f2937"}
        maskColor="rgba(15, 18, 25, 0.8)"
        style={{ backgroundColor: "#0f1219" }}
      />
    </ReactFlow>
  );
}

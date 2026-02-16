import type { Node, Edge, MarkerType } from "@xyflow/react";

// -- Interfaces -----------------------------------------------------------

export interface HypothesisNode {
  id: string;
  statement: string;
  status: "proposed" | "testing" | "supported" | "refuted" | "revised" | "rejected";
  parentId?: string;
  confidence?: number;
  rationale?: string;
  depth?: number;
}

export interface ExperimentNode {
  id: string;
  hypothesisId: string;
  description: string;
  status: "planned" | "running" | "completed" | "failed" | "awaiting_approval" | "paused" | "cancelled";
  tool_count?: number;
}

export interface FindingNode {
  id: string;
  hypothesisId: string;
  summary: string;
  evidenceType: "supporting" | "contradicting" | "neutral";
  detail?: string;
  source_id?: string; // Optional, to link to specific experiment if known
}

// -- Node data payload for custom InvestigationNode -----------------------

export interface InvestigationNodeData {
  label: string;
  sublabel: string;
  status: string;
  type: "hypothesis" | "experiment" | "finding" | "root";
  rationale?: string;
  confidence?: number;
  tool_count?: number;
  detail?: string;
  stroke: string;
  fill: string;
  textColor: string;
  [key: string]: unknown;
}

export interface DiagramData {
  nodes: Node<InvestigationNodeData>[];
  edges: Edge[];
}

// -- Tree Structure for Layout --------------------------------------------

interface TreeNode {
  id: string;
  type: 'hypothesis' | 'experiment' | 'root';
  data: any;
  children: TreeNode[];
  width: number;
  x: number;
  y: number;
  level: number;
}

// -- Constants ------------------------------------------------------------

const NODE_WIDTH = 260;
const CHILD_GAP = 50;
const LEVEL_HEIGHT = 200;
const SIDE_FINDING_WIDTH = 300;

const STATUS_STYLES: Record<string, { stroke: string; fill: string; text: string }> = {
  proposed: { stroke: "var(--color-muted-foreground)", fill: "var(--color-muted)", text: "var(--color-muted-foreground)" },
  testing: { stroke: "var(--color-accent)", fill: "color-mix(in srgb, var(--color-accent), transparent 90%)", text: "var(--color-accent)" },
  supported: { stroke: "var(--color-secondary)", fill: "color-mix(in srgb, var(--color-secondary), transparent 90%)", text: "var(--color-secondary)" },
  refuted: { stroke: "var(--color-destructive)", fill: "color-mix(in srgb, var(--color-destructive), transparent 90%)", text: "var(--color-destructive)" },
  revised: { stroke: "var(--color-primary)", fill: "color-mix(in srgb, var(--color-primary), transparent 90%)", text: "var(--color-primary)" },
  completed: { stroke: "var(--color-secondary)", fill: "var(--color-surface)", text: "var(--color-secondary)" },
  running: { stroke: "var(--color-primary)", fill: "var(--color-surface)", text: "var(--color-primary)" },
  neutral: { stroke: "var(--color-muted-foreground)", fill: "var(--color-surface)", text: "var(--color-muted-foreground)" },
  // Fallbacks
  planned: { stroke: "var(--color-muted-foreground)", fill: "var(--color-muted)", text: "var(--color-muted-foreground)" },
  failed: { stroke: "var(--color-destructive)", fill: "color-mix(in srgb, var(--color-destructive), transparent 90%)", text: "var(--color-destructive)" },
  awaiting_approval: { stroke: "var(--color-primary)", fill: "color-mix(in srgb, var(--color-primary), transparent 90%)", text: "var(--color-primary)" },
  paused: { stroke: "var(--color-indigo-500)", fill: "color-mix(in srgb, var(--color-indigo-500), transparent 90%)", text: "var(--color-indigo-500)" },
  cancelled: { stroke: "var(--color-muted-foreground)", fill: "var(--color-muted)", text: "var(--color-muted-foreground)" },
  supporting: { stroke: "var(--color-secondary)", fill: "color-mix(in srgb, var(--color-secondary), transparent 90%)", text: "var(--color-secondary)" },
  contradicting: { stroke: "var(--color-destructive)", fill: "color-mix(in srgb, var(--color-destructive), transparent 90%)", text: "var(--color-destructive)" },
};

// -- Main builder ---------------------------------------------------------

export function buildDiagramData(
  hypotheses: HypothesisNode[],
  experiments: ExperimentNode[],
  findings: FindingNode[],
): DiagramData {
  const nodes: Node<InvestigationNodeData>[] = [];


  // 1. Build Logical Tree
  function buildNode(id: string, type: 'hypothesis' | 'experiment' | 'root', level: number): TreeNode {
    let children: TreeNode[] = [];
    let data: any = {};

    if (type === 'root') {
      data = {
        type: 'root',
        label: "Research Goal", // We might want to pass the prompt here if available, but for now generic is fine or passed in props
        sublabel: "PROMPT",
        status: "neutral"
      };
      // Roots are hypotheses without parents
      const roots = hypotheses.filter(h => !h.parentId);
      children = roots.map(r => buildNode(r.id, 'hypothesis', level + 1));

    } else if (type === 'hypothesis') {
      data = hypotheses.find(h => h.id === id)!;
      // Children are Experiments testing this Hypothesis
      const exps = experiments.filter(e => e.hypothesisId === id);
      children = exps.map(e => buildNode(e.id, 'experiment', level + 1));

      data = { ...data }; // Clone
      data.type = 'hypothesis';
      data.label = data.statement;
      data.sublabel = data.status.toUpperCase();
      // Ensure specific fields
      data.rationale = data.rationale;
      data.confidence = data.confidence;

    } else if (type === 'experiment') {
      data = experiments.find(e => e.id === id)!;
      // Children are Revisions spawned by this Experiment
      // We look for hypotheses that have this experiment's hypothesis as parent.
      // Wait, in our data model:
      // Hypothesis(h1) -> Experiment(e1) -> Finding(f1)
      // Hypothesis(h1_v2) has parent_id = h1.
      // Logic: If h1_v2 is a revision of h1, it technically stems from h1's failure/result.
      // In the tree, we usually hang h1_v2 under e1 if e1 led to it?
      // Or just under h1?
      // debug.diagrams.tsx logic:
      // "Children are Revisions spawned by this Experiment"
      // const revisions = HYPOTHESES.filter(h => h.parentId === data.hypothesisId);
      // This hangs revisions under the experiment. This assumes the experiment led to the revision.
      const revisions = hypotheses.filter(h => h.parentId === data.hypothesisId);
      children = revisions.map(r => buildNode(r.id, 'hypothesis', level + 1));

      data = { ...data }; // Clone
      data.type = 'experiment';
      data.label = data.description;
      data.sublabel = data.status.toUpperCase();
      data.tool_count = data.tool_count;
    }

    return { id, type, data, children, width: 0, x: 0, y: 0, level };
  }

  // 2. Measure & Layout
  function measure(node: TreeNode) {
    if (node.children.length === 0) {
      node.width = NODE_WIDTH;
      if (node.type === 'experiment') {
        // Findings logic
        // In diagram-builder, we need to know if this experiment has findings
        // But findings might not be directly linked by ID if source_id is missing?
        // FindingNode has hypothesisId. It assumes findings belong to hypothesis?
        // debug.diagrams.tsx used 'source_id' linking to experiment.
        // We need to support both or infer.
        // If Finding has source_id, match experiment id.
        // If not, maybe match hypothesisId? But hypothesis has multiple experiments.
        // For now, let's look for findings with source_id === node.id OR (findings with matching hypothesisId if we assume 1:1?)
        // Let's stick to strict source_id or hypothesis fallback?
        // Actually, existing types.ts for Findings has 'source_id'.
        const nodeFindings = findings.filter(f => f.source_id === node.id || (f.hypothesisId === (node.data as ExperimentNode).hypothesisId && !f.source_id));

        if (nodeFindings.length > 0) {
          node.width += SIDE_FINDING_WIDTH;
        }
      }
    } else {
      let childrenWidth = 0;
      node.children.forEach((child, i) => {
        measure(child);
        childrenWidth += child.width;
        if (i < node.children.length - 1) childrenWidth += CHILD_GAP;
      });
      node.width = Math.max(NODE_WIDTH, childrenWidth);

      if (node.type === 'experiment') {
        const nodeFindings = findings.filter(f => f.source_id === node.id || (f.hypothesisId === (node.data as ExperimentNode).hypothesisId && !f.source_id));
        if (nodeFindings.length > 0) {
          const selfWidthWithFindings = NODE_WIDTH + SIDE_FINDING_WIDTH;
          node.width = Math.max(node.width, selfWidthWithFindings);
        }
      }
    }
  }

  function position(node: TreeNode, x: number) {
    let nodeX = x;

    if (node.children.length > 0) {
      let currentX = x;
      const childCenters: number[] = [];

      node.children.forEach(child => {
        childCenters.push(currentX + (child.width / 2));
        currentX += child.width + CHILD_GAP;
      });

      const firstChildCenter = childCenters[0];
      const lastChildCenter = childCenters[childCenters.length - 1];
      const blockCenter = (firstChildCenter + lastChildCenter) / 2;

      nodeX = blockCenter - (NODE_WIDTH / 2);
    } else {
      nodeX = x + (node.width / 2) - (NODE_WIDTH / 2);
    }

    node.x = nodeX;
    node.y = node.level * LEVEL_HEIGHT;

    let childXCursor = x;
    node.children.forEach(child => {
      position(child, childXCursor);
      childXCursor += child.width + CHILD_GAP;
    });
  }

  // 3. Render (Flatten to React Flow)
  const allRfEdges: Edge[] = [];

  function render(node: TreeNode) {
    const rfNodeId = node.id === 'root' ? 'root-prompt' : `tree-${node.id}`;

    nodes.push({
      id: rfNodeId,
      type: "investigation",
      position: { x: node.x, y: node.y + 50 },
      data: {
        ...node.data,
        type: node.type === 'root' ? 'root' : node.type,
        // Pass styles for safety, though component handles it too?
        // debug.diagrams.tsx component handles it based on status.
        // But we can pass explicitly if needed.
        // Let's rely on status in data.
      }
    });

    // Findings
    if (node.type === 'experiment') {
      // Logic for matching findings
      const nodeFindings = findings.filter(f => f.source_id === node.id || (f.hypothesisId === (node.data as ExperimentNode).hypothesisId && !f.source_id));

      if (nodeFindings.length > 0) {
        const findingX = node.x + NODE_WIDTH + 60;

        nodeFindings.forEach((f, fi) => {
          const findingY = node.y + 50 + (fi * 140);

          nodes.push({
            id: `tree-${f.id}`,
            type: "investigation",
            position: { x: findingX, y: findingY },
            data: {
              type: "finding",
              label: f.summary,
              sublabel: f.evidenceType.toUpperCase(),
              status: f.evidenceType,
              detail: f.detail,
              ...f
            } as any
          });

          allRfEdges.push({
            id: `t-fi-${node.id}-${f.id}`,
            source: rfNodeId,
            sourceHandle: "right",
            target: `tree-${f.id}`,
            targetHandle: "left",
            type: "smoothstep",
            style: { stroke: STATUS_STYLES[f.evidenceType]?.stroke || "#6b7280", strokeWidth: 1, strokeDasharray: "4 2" },
          });
        });
      }
    }

    // Children Edges
    node.children.forEach(child => {
      render(child);
      const childRfId = `tree-${child.id}`;

      let edgeType = "smoothstep";
      let style: any = { stroke: "var(--color-muted-foreground)", strokeWidth: 2 };
      let markerEnd = undefined;
      let label = undefined;
      let labelStyle = undefined;
      let strokeDasharray = undefined;

      if (node.type === 'root') {
        style = { stroke: "var(--color-muted-foreground)", strokeWidth: 1 };
      } else if (node.type === 'hypothesis') {
        label = "tested by";
        style = { stroke: "var(--color-foreground)", strokeWidth: 2 };
      } else if (node.type === 'experiment') {
        label = "led to revision";
        style = { stroke: "var(--color-primary)", strokeWidth: 2 };
        strokeDasharray = "5 5";
        markerEnd = { type: "arrowclosed" as MarkerType, color: "var(--color-primary)" }; // ReactFlow type string or object
        labelStyle = { fill: "var(--color-primary)", fontSize: 10, fontWeight: 700 };
      }

      allRfEdges.push({
        id: `e-${node.id}-${child.id}`,
        source: rfNodeId,
        sourceHandle: "bottom",
        target: childRfId,
        type: edgeType,
        label,
        style: { ...style, strokeDasharray },
        markerEnd,
        labelStyle
      });
    });
  }

  // Initial Root
  const rootNode = buildNode("root", "root", 0);
  measure(rootNode);
  position(rootNode, 0);
  render(rootNode);

  return { nodes, edges: allRfEdges };
}

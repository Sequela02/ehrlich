import type { Node, Edge } from "@xyflow/react";

export interface HypothesisNode {
  id: string;
  statement: string;
  status: "proposed" | "testing" | "supported" | "refuted" | "revised" | "rejected";
  parentId?: string;
  confidence?: number;
  depth?: number;
}

export interface ExperimentNode {
  id: string;
  hypothesisId: string;
  description: string;
  status: "planned" | "running" | "completed" | "failed" | "awaiting_approval" | "paused" | "cancelled";
}

export interface FindingNode {
  id: string;
  hypothesisId: string;
  summary: string;
  evidenceType: "supporting" | "contradicting" | "neutral";
}

// -- Node data payload for custom InvestigationNode -----------------------

export interface InvestigationNodeData {
  label: string;
  sublabel: string;
  stroke: string;
  fill: string;
  textColor: string;
  [key: string]: unknown;
}

export interface DiagramData {
  nodes: Node<InvestigationNodeData>[];
  edges: Edge[];
}

// -- Dark-friendly palette ------------------------------------------------

const STATUS_COLORS: Record<HypothesisNode["status"], { stroke: string; fill: string; text: string }> = {
  proposed: { stroke: "#6b7280", fill: "#1f2937", text: "#d1d5db" },
  testing: { stroke: "#3b82f6", fill: "#1e3a5f", text: "#93c5fd" },
  supported: { stroke: "#22c55e", fill: "#14532d", text: "#86efac" },
  refuted: { stroke: "#ef4444", fill: "#450a0a", text: "#fca5a5" },
  revised: { stroke: "#f59e0b", fill: "#451a03", text: "#fcd34d" },
  rejected: { stroke: "#374151", fill: "#111827", text: "#6b7280" },
};

const EXPERIMENT_COLORS: Record<ExperimentNode["status"], { stroke: string; fill: string; text: string }> = {
  planned: { stroke: "#6b7280", fill: "#1f2937", text: "#d1d5db" },
  running: { stroke: "#3b82f6", fill: "#1e3a5f", text: "#93c5fd" },
  completed: { stroke: "#22c55e", fill: "#14532d", text: "#86efac" },
  failed: { stroke: "#ef4444", fill: "#450a0a", text: "#fca5a5" },
  awaiting_approval: { stroke: "#f59e0b", fill: "#451a03", text: "#fcd34d" },
  paused: { stroke: "#6366f1", fill: "#1e1b4b", text: "#a5b4fc" },
  cancelled: { stroke: "#374151", fill: "#111827", text: "#6b7280" },
};

const EVIDENCE_COLORS: Record<FindingNode["evidenceType"], { stroke: string; fill: string; text: string }> = {
  supporting: { stroke: "#22c55e", fill: "#14532d", text: "#86efac" },
  contradicting: { stroke: "#ef4444", fill: "#450a0a", text: "#fca5a5" },
  neutral: { stroke: "#6b7280", fill: "#1f2937", text: "#d1d5db" },
};

const ARROW_LABELS: Record<string, string> = {
  revision: "revised to",
  experiment: "tested by",
  supporting: "supports",
  contradicting: "contradicts",
  neutral: "observed in",
};

// -- Layout constants -----------------------------------------------------

const NODE_W = 260;
const NODE_H = 80;
const H_GAP = 50;
const V_GAP = 120;
const LEFT_PAD = 50;

function truncate(text: string, maxLen: number): string {
  return text.length > maxLen ? text.slice(0, maxLen - 3) + "..." : text;
}

let edgeCounter = 0;
function nextEdgeId(): string {
  return `edge_${++edgeCounter}`;
}

// -- Main builder ---------------------------------------------------------

export function buildDiagramData(
  hypotheses: HypothesisNode[],
  experiments: ExperimentNode[],
  findings: FindingNode[],
): DiagramData {
  edgeCounter = 0;
  if (hypotheses.length === 0) {
    return { nodes: [], edges: [] };
  }

  const nodes: Node<InvestigationNodeData>[] = [];
  const edges: Edge[] = [];

  // ---- Row 1: Hypotheses ------------------------------------------------

  const HYP_Y = 50;

  // Section label node
  nodes.push({
    id: "label:hypotheses",
    type: "annotation",
    position: { x: LEFT_PAD, y: HYP_Y - 35 },
    data: { label: "HYPOTHESES", sublabel: "", stroke: "transparent", fill: "transparent", textColor: "#6b7280" },
    draggable: false,
    selectable: false,
  });

  hypotheses.forEach((h, i) => {
    const x = i * (NODE_W + H_GAP) + LEFT_PAD;
    const nodeId = `hyp:${h.id}`;
    const colors = STATUS_COLORS[h.status];

    const statusLine = h.confidence
      ? `${h.status.toUpperCase()} (${(h.confidence * 100).toFixed(0)}%)`
      : h.status.toUpperCase();

    nodes.push({
      id: nodeId,
      type: "investigation",
      position: { x, y: HYP_Y },
      data: {
        label: truncate(h.statement, 45),
        sublabel: statusLine,
        stroke: colors.stroke,
        fill: colors.fill,
        textColor: colors.text,
      },
      draggable: false,
    });

    if (h.parentId) {
      const parentId = `hyp:${h.parentId}`;
      const parentExists = hypotheses.some((ph) => ph.id === h.parentId);
      if (parentExists) {
        edges.push({
          id: nextEdgeId(),
          source: parentId,
          target: nodeId,
          label: ARROW_LABELS.revision,
          type: "smoothstep",
          style: { stroke: "#f59e0b", strokeDasharray: "6 4" },
          labelStyle: { fill: "#f59e0b", fontSize: 11 },
        });
      }
    }
  });

  // ---- Row 2: Experiments -----------------------------------------------

  const EXP_Y = HYP_Y + NODE_H + V_GAP;

  const expsByHypothesis = new Map<string, ExperimentNode[]>();
  for (const exp of experiments) {
    const list = expsByHypothesis.get(exp.hypothesisId) ?? [];
    list.push(exp);
    expsByHypothesis.set(exp.hypothesisId, list);
  }

  if (experiments.length > 0) {
    nodes.push({
      id: "label:experiments",
      type: "annotation",
      position: { x: LEFT_PAD, y: EXP_Y - 35 },
      data: { label: "EXPERIMENTS", sublabel: "", stroke: "transparent", fill: "transparent", textColor: "#6b7280" },
      draggable: false,
      selectable: false,
    });
  }

  let expIndex = 0;
  for (const [hId, exps] of expsByHypothesis) {
    const hNodeId = `hyp:${hId}`;

    for (const exp of exps) {
      const x = expIndex * (NODE_W + H_GAP) + LEFT_PAD;
      const nodeId = `exp:${exp.id}`;
      const colors = EXPERIMENT_COLORS[exp.status];

      nodes.push({
        id: nodeId,
        type: "investigation",
        position: { x, y: EXP_Y },
        data: {
          label: truncate(exp.description, 45),
          sublabel: exp.status.toUpperCase(),
          stroke: colors.stroke,
          fill: colors.fill,
          textColor: colors.text,
        },
        draggable: false,
      });

      edges.push({
        id: nextEdgeId(),
        source: hNodeId,
        target: nodeId,
        label: ARROW_LABELS.experiment,
        type: "smoothstep",
        style: { stroke: "#6b7280" },
        labelStyle: { fill: "#6b7280", fontSize: 11 },
      });

      expIndex++;
    }
  }

  // ---- Row 3: Findings --------------------------------------------------

  const FIND_Y = EXP_Y + NODE_H + V_GAP;

  const findingsByHypothesis = new Map<string, FindingNode[]>();
  for (const f of findings) {
    const list = findingsByHypothesis.get(f.hypothesisId) ?? [];
    list.push(f);
    findingsByHypothesis.set(f.hypothesisId, list);
  }

  if (findings.length > 0) {
    nodes.push({
      id: "label:findings",
      type: "annotation",
      position: { x: LEFT_PAD, y: FIND_Y - 35 },
      data: { label: "FINDINGS", sublabel: "", stroke: "transparent", fill: "transparent", textColor: "#6b7280" },
      draggable: false,
      selectable: false,
    });
  }

  let findIndex = 0;
  for (const [hId, fs] of findingsByHypothesis) {
    const linkedExpId = experiments.find((e) => e.hypothesisId === hId)?.id;
    const parentId = linkedExpId ? `exp:${linkedExpId}` : undefined;

    for (const f of fs) {
      const x = findIndex * (NODE_W + H_GAP) + LEFT_PAD;
      const nodeId = `find:${f.id}`;
      const colors = EVIDENCE_COLORS[f.evidenceType];

      nodes.push({
        id: nodeId,
        type: "investigation",
        position: { x, y: FIND_Y },
        data: {
          label: truncate(f.summary, 45),
          sublabel: f.evidenceType.toUpperCase(),
          stroke: colors.stroke,
          fill: colors.fill,
          textColor: colors.text,
        },
        draggable: false,
      });

      if (parentId) {
        edges.push({
          id: nextEdgeId(),
          source: parentId,
          target: nodeId,
          label: ARROW_LABELS[f.evidenceType] ?? f.evidenceType,
          type: "smoothstep",
          style: { stroke: colors.stroke },
          labelStyle: { fill: colors.stroke, fontSize: 11 },
        });
      }

      findIndex++;
    }
  }

  return { nodes, edges };
}

import type { ExcalidrawElementSkeleton } from "@excalidraw/excalidraw/data/transform";

export interface HypothesisNode {
  id: string;
  statement: string;
  status: "proposed" | "testing" | "supported" | "refuted" | "revised";
  parentId?: string;
  confidence?: number;
}

export interface ExperimentNode {
  id: string;
  hypothesisId: string;
  description: string;
  status: "planned" | "running" | "completed" | "failed";
}

export interface FindingNode {
  id: string;
  hypothesisId: string;
  summary: string;
  evidenceType: "supporting" | "contradicting" | "neutral";
}

const STATUS_COLORS: Record<HypothesisNode["status"], string> = {
  proposed: "#6b7280",
  testing: "#3b82f6",
  supported: "#22c55e",
  refuted: "#ef4444",
  revised: "#f97316",
};

const EXPERIMENT_COLORS: Record<ExperimentNode["status"], string> = {
  planned: "#6b7280",
  running: "#3b82f6",
  completed: "#22c55e",
  failed: "#ef4444",
};

const EVIDENCE_COLORS: Record<FindingNode["evidenceType"], string> = {
  supporting: "#22c55e",
  contradicting: "#ef4444",
  neutral: "#6b7280",
};

const NODE_W = 240;
const NODE_H = 80;
const H_GAP = 40;
const V_GAP = 60;

let idCounter = 0;
function nextId(): string {
  return `diag_${++idCounter}`;
}

function truncate(text: string, maxLen: number): string {
  return text.length > maxLen ? text.slice(0, maxLen - 3) + "..." : text;
}

export function buildDiagramElements(
  hypotheses: HypothesisNode[],
  experiments: ExperimentNode[],
  findings: FindingNode[],
): ExcalidrawElementSkeleton[] {
  idCounter = 0;
  const elements: ExcalidrawElementSkeleton[] = [];
  const hypothesisPositions = new Map<string, { x: number; y: number; id: string }>();

  const ROW_Y = 40;
  hypotheses.forEach((h, i) => {
    const x = i * (NODE_W + H_GAP) + 40;
    const y = ROW_Y;
    const rectId = nextId();

    hypothesisPositions.set(h.id, { x, y, id: rectId });

    elements.push({
      type: "rectangle",
      id: rectId,
      x,
      y,
      width: NODE_W,
      height: NODE_H,
      strokeColor: STATUS_COLORS[h.status],
      backgroundColor: STATUS_COLORS[h.status] + "20",
      fillStyle: "solid",
      roundness: { type: 3 },
    } as ExcalidrawElementSkeleton);

    elements.push({
      type: "text",
      id: nextId(),
      x: x + 10,
      y: y + 10,
      width: NODE_W - 20,
      height: 20,
      text: truncate(h.statement, 50),
      fontSize: 14,
      strokeColor: "#e2e8f0",
    } as ExcalidrawElementSkeleton);

    const statusLabel = h.confidence
      ? `${h.status} (${(h.confidence * 100).toFixed(0)}%)`
      : h.status;
    elements.push({
      type: "text",
      id: nextId(),
      x: x + 10,
      y: y + NODE_H - 28,
      width: NODE_W - 20,
      height: 16,
      text: statusLabel,
      fontSize: 12,
      strokeColor: STATUS_COLORS[h.status],
    } as ExcalidrawElementSkeleton);

    if (h.parentId) {
      const parentPos = hypothesisPositions.get(h.parentId);
      if (parentPos) {
        elements.push({
          type: "arrow",
          id: nextId(),
          x: parentPos.x + NODE_W / 2,
          y: parentPos.y + NODE_H,
          width: x + NODE_W / 2 - (parentPos.x + NODE_W / 2),
          height: y - (parentPos.y + NODE_H),
          strokeColor: "#f97316",
          start: { id: parentPos.id, type: "rectangle" },
          end: { id: rectId, type: "rectangle" },
        } as ExcalidrawElementSkeleton);
      }
    }
  });

  const EXP_Y = ROW_Y + NODE_H + V_GAP;
  const expPositions = new Map<string, { x: number; y: number; id: string }>();
  const expsByHypothesis = new Map<string, ExperimentNode[]>();

  for (const exp of experiments) {
    const list = expsByHypothesis.get(exp.hypothesisId) ?? [];
    list.push(exp);
    expsByHypothesis.set(exp.hypothesisId, list);
  }

  let expIndex = 0;
  for (const [hId, exps] of expsByHypothesis) {
    const hPos = hypothesisPositions.get(hId);

    for (const exp of exps) {
      const x = expIndex * (NODE_W + H_GAP) + 40;
      const y = EXP_Y;
      const rectId = nextId();

      expPositions.set(exp.id, { x, y, id: rectId });

      elements.push({
        type: "rectangle",
        id: rectId,
        x,
        y,
        width: NODE_W,
        height: NODE_H,
        strokeColor: EXPERIMENT_COLORS[exp.status],
        backgroundColor: EXPERIMENT_COLORS[exp.status] + "15",
        fillStyle: "solid",
        roundness: { type: 3 },
      } as ExcalidrawElementSkeleton);

      elements.push({
        type: "text",
        id: nextId(),
        x: x + 10,
        y: y + 10,
        width: NODE_W - 20,
        height: 20,
        text: truncate(exp.description, 50),
        fontSize: 13,
        strokeColor: "#cbd5e1",
      } as ExcalidrawElementSkeleton);

      elements.push({
        type: "text",
        id: nextId(),
        x: x + 10,
        y: y + NODE_H - 26,
        width: NODE_W - 20,
        height: 16,
        text: exp.status,
        fontSize: 11,
        strokeColor: EXPERIMENT_COLORS[exp.status],
      } as ExcalidrawElementSkeleton);

      if (hPos) {
        elements.push({
          type: "arrow",
          id: nextId(),
          x: hPos.x + NODE_W / 2,
          y: hPos.y + NODE_H,
          width: x + NODE_W / 2 - (hPos.x + NODE_W / 2),
          height: y - (hPos.y + NODE_H),
          strokeColor: "#475569",
          start: { id: hPos.id, type: "rectangle" },
          end: { id: rectId, type: "rectangle" },
        } as ExcalidrawElementSkeleton);
      }

      expIndex++;
    }
  }

  const FIND_Y = EXP_Y + NODE_H + V_GAP;
  const findingsByHypothesis = new Map<string, FindingNode[]>();

  for (const f of findings) {
    const list = findingsByHypothesis.get(f.hypothesisId) ?? [];
    list.push(f);
    findingsByHypothesis.set(f.hypothesisId, list);
  }

  let findIndex = 0;
  for (const [hId, fs] of findingsByHypothesis) {
    for (const f of fs) {
      const x = findIndex * (NODE_W + H_GAP) + 40;
      const y = FIND_Y;
      const rectId = nextId();

      elements.push({
        type: "rectangle",
        id: rectId,
        x,
        y,
        width: NODE_W,
        height: NODE_H,
        strokeColor: EVIDENCE_COLORS[f.evidenceType],
        backgroundColor: EVIDENCE_COLORS[f.evidenceType] + "15",
        fillStyle: "solid",
        roundness: { type: 3 },
      } as ExcalidrawElementSkeleton);

      elements.push({
        type: "text",
        id: nextId(),
        x: x + 10,
        y: y + 10,
        width: NODE_W - 20,
        height: 20,
        text: truncate(f.summary, 50),
        fontSize: 13,
        strokeColor: "#cbd5e1",
      } as ExcalidrawElementSkeleton);

      elements.push({
        type: "text",
        id: nextId(),
        x: x + 10,
        y: y + NODE_H - 26,
        width: NODE_W - 20,
        height: 16,
        text: f.evidenceType,
        fontSize: 11,
        strokeColor: EVIDENCE_COLORS[f.evidenceType],
      } as ExcalidrawElementSkeleton);

      const linkedExpIds = experiments
        .filter((e) => e.hypothesisId === hId)
        .map((e) => e.id);

      const closestExp = linkedExpIds
        .map((eid) => expPositions.get(eid))
        .filter(Boolean)[0];

      if (closestExp) {
        elements.push({
          type: "arrow",
          id: nextId(),
          x: closestExp.x + NODE_W / 2,
          y: closestExp.y + NODE_H,
          width: x + NODE_W / 2 - (closestExp.x + NODE_W / 2),
          height: y - (closestExp.y + NODE_H),
          strokeColor: EVIDENCE_COLORS[f.evidenceType],
          start: { id: closestExp.id, type: "rectangle" },
          end: { id: rectId, type: "rectangle" },
        } as ExcalidrawElementSkeleton);
      }

      findIndex++;
    }
  }

  return elements;
}

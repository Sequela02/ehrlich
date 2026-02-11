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

// -- Excalidraw semantic palette (professional, dark-friendly) --------

const STATUS_COLORS: Record<HypothesisNode["status"], { stroke: string; bg: string }> = {
  proposed: { stroke: "#868e96", bg: "#e9ecef" },
  testing:  { stroke: "#1971c2", bg: "#a5d8ff" },
  supported: { stroke: "#2f9e44", bg: "#b2f2bb" },
  refuted:  { stroke: "#e03131", bg: "#ffc9c9" },
  revised:  { stroke: "#f08c00", bg: "#ffec99" },
};

const EXPERIMENT_COLORS: Record<ExperimentNode["status"], { stroke: string; bg: string }> = {
  planned:   { stroke: "#868e96", bg: "#e9ecef" },
  running:   { stroke: "#1971c2", bg: "#a5d8ff" },
  completed: { stroke: "#2f9e44", bg: "#b2f2bb" },
  failed:    { stroke: "#e03131", bg: "#ffc9c9" },
};

const EVIDENCE_COLORS: Record<FindingNode["evidenceType"], { stroke: string; bg: string }> = {
  supporting:    { stroke: "#2f9e44", bg: "#b2f2bb" },
  contradicting: { stroke: "#e03131", bg: "#ffc9c9" },
  neutral:       { stroke: "#868e96", bg: "#e9ecef" },
};

const ARROW_LABELS: Record<string, string> = {
  revision: "revised to",
  experiment: "tested by",
  supporting: "supports",
  contradicting: "contradicts",
  neutral: "observed in",
};

// -- Layout constants -------------------------------------------------

const NODE_W = 260;
const NODE_H = 80;
const H_GAP = 50;
const V_GAP = 100;
const LEFT_PAD = 50;

// -- Shared element defaults (clean, professional) --------------------

const BASE = {
  roughness: 0 as const,
  strokeWidth: 2 as const,
  fillStyle: "solid" as const,
  roundness: { type: 3 as const },
};

const FONT = {
  fontFamily: 2 as const,
  textAlign: "center" as const,
  verticalAlign: "middle" as const,
};

// -- ID generator (reset per call) ------------------------------------

let idCounter = 0;
function nextId(): string {
  return `diag_${++idCounter}`;
}

function truncate(text: string, maxLen: number): string {
  return text.length > maxLen ? text.slice(0, maxLen - 3) + "..." : text;
}

// -- Section title (locked text label) --------------------------------

function sectionTitle(text: string, x: number, y: number): ExcalidrawElementSkeleton {
  return {
    type: "text",
    id: nextId(),
    x,
    y: y - 30,
    text,
    fontSize: 16,
    fontFamily: 2,
    strokeColor: "#868e96",
    locked: true,
  } as ExcalidrawElementSkeleton;
}

// -- Arrow with computed position + id binding ------------------------

interface Pos { x: number; y: number; id: string }

function arrow(
  from: Pos,
  to: Pos,
  color: string,
  labelText?: string,
  dashed?: boolean,
): ExcalidrawElementSkeleton {
  const startX = from.x + NODE_W / 2;
  const startY = from.y + NODE_H;
  const endX = to.x + NODE_W / 2;
  const endY = to.y;

  return {
    type: "arrow",
    id: nextId(),
    x: startX,
    y: startY,
    width: endX - startX,
    height: endY - startY,
    points: [[0, 0], [endX - startX, endY - startY]],
    strokeColor: color,
    strokeStyle: dashed ? "dashed" : "solid",
    endArrowhead: "arrow",
    startBinding: { elementId: from.id, focus: 0, gap: 5 },
    endBinding: { elementId: to.id, focus: 0, gap: 5 },
    ...BASE,
    roundness: null,
    ...(labelText
      ? { label: { text: labelText, fontSize: 12, ...FONT } }
      : {}),
  } as ExcalidrawElementSkeleton;
}

// -- Main builder -----------------------------------------------------

export function buildDiagramElements(
  hypotheses: HypothesisNode[],
  experiments: ExperimentNode[],
  findings: FindingNode[],
): ExcalidrawElementSkeleton[] {
  idCounter = 0;
  if (hypotheses.length === 0) return [];

  const elements: ExcalidrawElementSkeleton[] = [];
  const nodePositions = new Map<string, Pos>();

  // ---- Row 1: Hypotheses --------------------------------------------

  const HYP_Y = 60;
  elements.push(sectionTitle("HYPOTHESES", LEFT_PAD, HYP_Y));

  hypotheses.forEach((h, i) => {
    const x = i * (NODE_W + H_GAP) + LEFT_PAD;
    const rectId = nextId();
    nodePositions.set(`hyp:${h.id}`, { x, y: HYP_Y, id: rectId });
    const colors = STATUS_COLORS[h.status];

    const statusLine = h.confidence
      ? `${h.status.toUpperCase()} (${(h.confidence * 100).toFixed(0)}%)`
      : h.status.toUpperCase();

    elements.push({
      type: "rectangle",
      id: rectId,
      x,
      y: HYP_Y,
      width: NODE_W,
      height: NODE_H,
      strokeColor: colors.stroke,
      backgroundColor: colors.bg,
      label: {
        text: `${truncate(h.statement, 45)}\n${statusLine}`,
        fontSize: 14,
        ...FONT,
        strokeColor: "#1e1e1e",
      },
      ...BASE,
    } as ExcalidrawElementSkeleton);

    if (h.parentId) {
      const parentPos = nodePositions.get(`hyp:${h.parentId}`);
      if (parentPos) {
        const pos = nodePositions.get(`hyp:${h.id}`)!;
        elements.push(arrow(parentPos, pos, "#f08c00", ARROW_LABELS.revision, true));
      }
    }
  });

  // ---- Row 2: Experiments -------------------------------------------

  const EXP_Y = HYP_Y + NODE_H + V_GAP;

  const expsByHypothesis = new Map<string, ExperimentNode[]>();
  for (const exp of experiments) {
    const list = expsByHypothesis.get(exp.hypothesisId) ?? [];
    list.push(exp);
    expsByHypothesis.set(exp.hypothesisId, list);
  }

  if (experiments.length > 0) {
    elements.push(sectionTitle("EXPERIMENTS", LEFT_PAD, EXP_Y));
  }

  let expIndex = 0;
  for (const [hId, exps] of expsByHypothesis) {
    const hPos = nodePositions.get(`hyp:${hId}`);

    for (const exp of exps) {
      const x = expIndex * (NODE_W + H_GAP) + LEFT_PAD;
      const rectId = nextId();
      nodePositions.set(`exp:${exp.id}`, { x, y: EXP_Y, id: rectId });
      const colors = EXPERIMENT_COLORS[exp.status];

      elements.push({
        type: "rectangle",
        id: rectId,
        x,
        y: EXP_Y,
        width: NODE_W,
        height: NODE_H,
        strokeColor: colors.stroke,
        backgroundColor: colors.bg,
        label: {
          text: `${truncate(exp.description, 45)}\n${exp.status.toUpperCase()}`,
          fontSize: 13,
          ...FONT,
          strokeColor: "#1e1e1e",
        },
        ...BASE,
      } as ExcalidrawElementSkeleton);

      if (hPos) {
        const expPos = nodePositions.get(`exp:${exp.id}`)!;
        elements.push(arrow(hPos, expPos, "#868e96", ARROW_LABELS.experiment));
      }

      expIndex++;
    }
  }

  // ---- Row 3: Findings ----------------------------------------------

  const FIND_Y = EXP_Y + NODE_H + V_GAP;

  const findingsByHypothesis = new Map<string, FindingNode[]>();
  for (const f of findings) {
    const list = findingsByHypothesis.get(f.hypothesisId) ?? [];
    list.push(f);
    findingsByHypothesis.set(f.hypothesisId, list);
  }

  if (findings.length > 0) {
    elements.push(sectionTitle("FINDINGS", LEFT_PAD, FIND_Y));
  }

  let findIndex = 0;
  for (const [hId, fs] of findingsByHypothesis) {
    const linkedExpId = experiments.find((e) => e.hypothesisId === hId)?.id;
    const parentPos = linkedExpId
      ? nodePositions.get(`exp:${linkedExpId}`)
      : undefined;

    for (const f of fs) {
      const x = findIndex * (NODE_W + H_GAP) + LEFT_PAD;
      const rectId = nextId();
      const colors = EVIDENCE_COLORS[f.evidenceType];

      elements.push({
        type: "rectangle",
        id: rectId,
        x,
        y: FIND_Y,
        width: NODE_W,
        height: NODE_H,
        strokeColor: colors.stroke,
        backgroundColor: colors.bg,
        label: {
          text: `${truncate(f.summary, 45)}\n${f.evidenceType.toUpperCase()}`,
          fontSize: 13,
          ...FONT,
          strokeColor: "#1e1e1e",
        },
        ...BASE,
      } as ExcalidrawElementSkeleton);

      if (parentPos) {
        const findPos: Pos = { x, y: FIND_Y, id: rectId };
        elements.push(
          arrow(
            parentPos,
            findPos,
            colors.stroke,
            ARROW_LABELS[f.evidenceType] ?? f.evidenceType,
          ),
        );
      }

      findIndex++;
    }
  }

  return elements;
}

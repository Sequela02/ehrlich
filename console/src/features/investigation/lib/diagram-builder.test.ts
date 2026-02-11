import { describe, it, expect } from "vitest";
import {
  buildDiagramElements,
  type HypothesisNode,
  type ExperimentNode,
  type FindingNode,
} from "./diagram-builder";

function makeHypothesis(overrides: Partial<HypothesisNode> = {}): HypothesisNode {
  return {
    id: "h1",
    statement: "Test hypothesis",
    status: "proposed",
    ...overrides,
  };
}

function makeExperiment(overrides: Partial<ExperimentNode> = {}): ExperimentNode {
  return {
    id: "e1",
    hypothesisId: "h1",
    description: "Test experiment",
    status: "completed",
    ...overrides,
  };
}

function makeFinding(overrides: Partial<FindingNode> = {}): FindingNode {
  return {
    id: "f1",
    hypothesisId: "h1",
    summary: "Test finding",
    evidenceType: "supporting",
    ...overrides,
  };
}

function getRects(elements: ReturnType<typeof buildDiagramElements>) {
  return elements.filter((e) => e.type === "rectangle");
}

function getArrows(elements: ReturnType<typeof buildDiagramElements>) {
  return elements.filter((e) => e.type === "arrow");
}

function getTexts(elements: ReturnType<typeof buildDiagramElements>) {
  return elements.filter((e) => e.type === "text");
}

describe("buildDiagramElements", () => {
  it("returns empty array for no data", () => {
    const elements = buildDiagramElements([], [], []);
    expect(elements).toEqual([]);
  });

  it("creates rectangle with label for hypothesis (no separate text elements)", () => {
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const rects = getRects(elements);
    expect(rects).toHaveLength(1);
    const rect = rects[0] as Record<string, unknown>;
    expect(rect.label).toBeDefined();
    const label = rect.label as Record<string, unknown>;
    expect((label.text as string)).toContain("Test hypothesis");
  });

  it("adds section title as locked text", () => {
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const texts = getTexts(elements);
    expect(texts.length).toBeGreaterThanOrEqual(1);
    const title = texts[0] as Record<string, unknown>;
    expect(title.text).toBe("HYPOTHESES");
    expect(title.locked).toBe(true);
  });

  it("applies correct status color to hypothesis", () => {
    const elements = buildDiagramElements(
      [makeHypothesis({ status: "supported" })],
      [],
      [],
    );
    const rect = getRects(elements)[0] as Record<string, unknown>;
    expect(rect.strokeColor).toBe("#2f9e44");
    expect(rect.backgroundColor).toBe("#b2f2bb");
  });

  it("uses clean professional defaults (roughness 0, strokeWidth 2)", () => {
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const rect = getRects(elements)[0] as Record<string, unknown>;
    expect(rect.roughness).toBe(0);
    expect(rect.strokeWidth).toBe(2);
    expect(rect.fillStyle).toBe("solid");
  });

  it("uses Helvetica font in labels", () => {
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const rect = getRects(elements)[0] as Record<string, unknown>;
    const label = rect.label as Record<string, unknown>;
    expect(label.fontFamily).toBe(2);
  });

  it("truncates long hypothesis statements", () => {
    const longStatement = "A".repeat(60);
    const elements = buildDiagramElements(
      [makeHypothesis({ statement: longStatement })],
      [],
      [],
    );
    const rect = getRects(elements)[0] as Record<string, unknown>;
    const label = rect.label as Record<string, unknown>;
    const firstLine = (label.text as string).split("\n")[0];
    expect(firstLine.length).toBeLessThanOrEqual(45);
    expect(firstLine.endsWith("...")).toBe(true);
  });

  it("shows confidence in status line", () => {
    const elements = buildDiagramElements(
      [makeHypothesis({ status: "supported", confidence: 0.85 })],
      [],
      [],
    );
    const rect = getRects(elements)[0] as Record<string, unknown>;
    const label = rect.label as Record<string, unknown>;
    expect((label.text as string)).toContain("SUPPORTED (85%)");
  });

  it("creates dashed arrow between parent and revised hypothesis with label", () => {
    const hyps = [
      makeHypothesis({ id: "h1", status: "refuted" }),
      makeHypothesis({ id: "h2", status: "revised", parentId: "h1" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const arrows = getArrows(elements);
    expect(arrows).toHaveLength(1);
    const a = arrows[0] as Record<string, unknown>;
    expect(a.strokeColor).toBe("#f08c00");
    expect(a.strokeStyle).toBe("dashed");
    const label = a.label as Record<string, unknown>;
    expect(label.text).toBe("revised to");
  });

  it("uses computed positions with element binding on arrows", () => {
    const hyps = [
      makeHypothesis({ id: "h1" }),
      makeHypothesis({ id: "h2", parentId: "h1" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const a = getArrows(elements)[0] as Record<string, unknown>;
    const startBinding = a.startBinding as Record<string, unknown>;
    const endBinding = a.endBinding as Record<string, unknown>;
    expect(startBinding.elementId).toBeDefined();
    expect(endBinding.elementId).toBeDefined();
    expect(a.x).not.toBe(0);
    expect(a.points).toBeDefined();
  });

  it("skips arrow when parentId references non-existent hypothesis", () => {
    const hyps = [makeHypothesis({ id: "h2", parentId: "h_nonexistent" })];
    const elements = buildDiagramElements(hyps, [], []);
    const arrows = getArrows(elements);
    expect(arrows).toHaveLength(0);
  });

  it("creates experiment nodes with labeled arrow to hypothesis", () => {
    const hyps = [makeHypothesis()];
    const exps = [makeExperiment()];
    const elements = buildDiagramElements(hyps, exps, []);
    const rects = getRects(elements);
    const arrows = getArrows(elements);
    expect(rects).toHaveLength(2);
    expect(arrows).toHaveLength(1);
    const arrowLabel = (arrows[0] as Record<string, unknown>).label as Record<string, unknown>;
    expect(arrowLabel.text).toBe("tested by");
  });

  it("adds EXPERIMENTS section title when experiments exist", () => {
    const elements = buildDiagramElements(
      [makeHypothesis()],
      [makeExperiment()],
      [],
    );
    const texts = getTexts(elements);
    const expTitle = texts.find((t) => (t as Record<string, unknown>).text === "EXPERIMENTS");
    expect(expTitle).toBeDefined();
  });

  it("creates finding nodes with evidence-labeled arrow", () => {
    const hyps = [makeHypothesis()];
    const exps = [makeExperiment()];
    const finds = [makeFinding()];
    const elements = buildDiagramElements(hyps, exps, finds);
    const rects = getRects(elements);
    const arrows = getArrows(elements);
    expect(rects).toHaveLength(3);
    expect(arrows).toHaveLength(2);
    const findingArrow = arrows[arrows.length - 1] as Record<string, unknown>;
    const label = findingArrow.label as Record<string, unknown>;
    expect(label.text).toBe("supports");
  });

  it("uses contradicting color and label for contradicting findings", () => {
    const elements = buildDiagramElements(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding({ evidenceType: "contradicting" })],
    );
    const arrows = getArrows(elements);
    const findingArrow = arrows[arrows.length - 1] as Record<string, unknown>;
    expect(findingArrow.strokeColor).toBe("#e03131");
    const label = findingArrow.label as Record<string, unknown>;
    expect(label.text).toBe("contradicts");
  });

  it("positions hypotheses in a row with correct spacing", () => {
    const hyps = [
      makeHypothesis({ id: "h1" }),
      makeHypothesis({ id: "h2" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const rects = getRects(elements);
    const x1 = (rects[0] as Record<string, unknown>).x as number;
    const x2 = (rects[1] as Record<string, unknown>).x as number;
    expect(x2 - x1).toBe(260 + 50);
  });

  it("handles full graph with multiple nodes", () => {
    const hyps = [
      makeHypothesis({ id: "h1" }),
      makeHypothesis({ id: "h2" }),
    ];
    const exps = [
      makeExperiment({ id: "e1", hypothesisId: "h1" }),
      makeExperiment({ id: "e2", hypothesisId: "h2" }),
    ];
    const finds = [
      makeFinding({ id: "f1", hypothesisId: "h1" }),
      makeFinding({ id: "f2", hypothesisId: "h2", evidenceType: "contradicting" }),
    ];
    const elements = buildDiagramElements(hyps, exps, finds);
    const rects = getRects(elements);
    const arrows = getArrows(elements);
    expect(rects).toHaveLength(6);
    expect(arrows).toHaveLength(4);
  });

  it("resets ID counter between calls", () => {
    buildDiagramElements([makeHypothesis()], [], []);
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const texts = getTexts(elements);
    expect((texts[0] as Record<string, unknown>).id).toBe("diag_1");
  });
});

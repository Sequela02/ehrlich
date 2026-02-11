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

describe("buildDiagramElements", () => {
  it("returns empty array for no data", () => {
    const elements = buildDiagramElements([], [], []);
    expect(elements).toEqual([]);
  });

  it("creates rectangle + 2 text elements per hypothesis", () => {
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const texts = elements.filter((e) => e.type === "text");
    expect(rectangles).toHaveLength(1);
    expect(texts).toHaveLength(2);
  });

  it("applies correct status color to hypothesis", () => {
    const elements = buildDiagramElements(
      [makeHypothesis({ status: "supported" })],
      [],
      [],
    );
    const rect = elements.find((e) => e.type === "rectangle");
    expect(rect).toBeDefined();
    expect((rect as Record<string, unknown>).strokeColor).toBe("#22c55e");
  });

  it("truncates long hypothesis statements", () => {
    const longStatement = "A".repeat(60);
    const elements = buildDiagramElements(
      [makeHypothesis({ statement: longStatement })],
      [],
      [],
    );
    const texts = elements.filter((e) => e.type === "text");
    const statementText = texts[0] as Record<string, unknown>;
    expect((statementText.text as string).length).toBeLessThanOrEqual(50);
    expect((statementText.text as string).endsWith("...")).toBe(true);
  });

  it("shows confidence in status label", () => {
    const elements = buildDiagramElements(
      [makeHypothesis({ status: "supported", confidence: 0.85 })],
      [],
      [],
    );
    const texts = elements.filter((e) => e.type === "text");
    const statusText = texts[1] as Record<string, unknown>;
    expect(statusText.text).toBe("supported (85%)");
  });

  it("creates arrow between parent and revised hypothesis", () => {
    const hyps = [
      makeHypothesis({ id: "h1", status: "refuted" }),
      makeHypothesis({ id: "h2", status: "revised", parentId: "h1" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const arrows = elements.filter((e) => e.type === "arrow");
    expect(arrows).toHaveLength(1);
    expect((arrows[0] as Record<string, unknown>).strokeColor).toBe("#f97316");
  });

  it("skips arrow when parentId references non-existent hypothesis", () => {
    const hyps = [
      makeHypothesis({ id: "h2", parentId: "h_nonexistent" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const arrows = elements.filter((e) => e.type === "arrow");
    expect(arrows).toHaveLength(0);
  });

  it("creates experiment nodes with arrow to hypothesis", () => {
    const hyps = [makeHypothesis()];
    const exps = [makeExperiment()];
    const elements = buildDiagramElements(hyps, exps, []);
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const arrows = elements.filter((e) => e.type === "arrow");
    expect(rectangles).toHaveLength(2);
    expect(arrows).toHaveLength(1);
  });

  it("applies correct status color to experiment", () => {
    const elements = buildDiagramElements(
      [makeHypothesis()],
      [makeExperiment({ status: "failed" })],
      [],
    );
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const expRect = rectangles[1] as Record<string, unknown>;
    expect(expRect.strokeColor).toBe("#ef4444");
  });

  it("creates finding nodes with arrow to experiment", () => {
    const hyps = [makeHypothesis()];
    const exps = [makeExperiment()];
    const finds = [makeFinding()];
    const elements = buildDiagramElements(hyps, exps, finds);
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const arrows = elements.filter((e) => e.type === "arrow");
    expect(rectangles).toHaveLength(3);
    expect(arrows).toHaveLength(2);
  });

  it("applies evidence type color to finding arrow", () => {
    const elements = buildDiagramElements(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding({ evidenceType: "contradicting" })],
    );
    const arrows = elements.filter((e) => e.type === "arrow");
    const findingArrow = arrows[arrows.length - 1] as Record<string, unknown>;
    expect(findingArrow.strokeColor).toBe("#ef4444");
  });

  it("positions hypotheses in a row with correct spacing", () => {
    const hyps = [
      makeHypothesis({ id: "h1" }),
      makeHypothesis({ id: "h2" }),
    ];
    const elements = buildDiagramElements(hyps, [], []);
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const x1 = (rectangles[0] as Record<string, unknown>).x as number;
    const x2 = (rectangles[1] as Record<string, unknown>).x as number;
    expect(x2 - x1).toBe(240 + 40);
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
    const rectangles = elements.filter((e) => e.type === "rectangle");
    const arrows = elements.filter((e) => e.type === "arrow");
    expect(rectangles).toHaveLength(6);
    expect(arrows).toHaveLength(4);
  });

  it("resets ID counter between calls", () => {
    buildDiagramElements([makeHypothesis()], [], []);
    const elements = buildDiagramElements([makeHypothesis()], [], []);
    const rect = elements.find((e) => e.type === "rectangle");
    expect((rect as Record<string, unknown>).id).toBe("diag_1");
  });
});

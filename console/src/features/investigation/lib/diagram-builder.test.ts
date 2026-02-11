import { describe, it, expect } from "vitest";
import {
  buildDiagramData,
  type HypothesisNode,
  type ExperimentNode,
  type FindingNode,
  type DiagramData,
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

function getInvestigationNodes(data: DiagramData) {
  return data.nodes.filter((n) => n.type === "investigation");
}

function getAnnotationNodes(data: DiagramData) {
  return data.nodes.filter((n) => n.type === "annotation");
}

describe("buildDiagramData", () => {
  it("returns empty data for no hypotheses", () => {
    const data = buildDiagramData([], [], []);
    expect(data.nodes).toEqual([]);
    expect(data.edges).toEqual([]);
  });

  it("creates investigation node with correct data for hypothesis", () => {
    const data = buildDiagramData([makeHypothesis()], [], []);
    const nodes = getInvestigationNodes(data);
    expect(nodes).toHaveLength(1);
    expect(nodes[0].id).toBe("hyp:h1");
    expect(nodes[0].type).toBe("investigation");
    expect(nodes[0].data.label).toContain("Test hypothesis");
    expect(nodes[0].data.sublabel).toBe("PROPOSED");
    expect(nodes[0].position).toBeDefined();
  });

  it("applies correct status colors (dark-friendly)", () => {
    const data = buildDiagramData(
      [makeHypothesis({ status: "supported" })],
      [],
      [],
    );
    const node = getInvestigationNodes(data)[0];
    expect(node.data.stroke).toBe("#22c55e");
    expect(node.data.fill).toBe("#14532d");
    expect(node.data.textColor).toBe("#86efac");
  });

  it("truncates long statements", () => {
    const longStatement = "A".repeat(60);
    const data = buildDiagramData(
      [makeHypothesis({ statement: longStatement })],
      [],
      [],
    );
    const node = getInvestigationNodes(data)[0];
    expect(node.data.label.length).toBeLessThanOrEqual(45);
    expect(node.data.label.endsWith("...")).toBe(true);
  });

  it("shows confidence in sublabel", () => {
    const data = buildDiagramData(
      [makeHypothesis({ status: "supported", confidence: 0.85 })],
      [],
      [],
    );
    const node = getInvestigationNodes(data)[0];
    expect(node.data.sublabel).toBe("SUPPORTED (85%)");
  });

  it("creates section label annotations", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding()],
    );
    const annotations = getAnnotationNodes(data);
    expect(annotations).toHaveLength(3);
    expect(annotations.map((a) => a.data.label)).toEqual(["HYPOTHESES", "EXPERIMENTS", "FINDINGS"]);
  });

  it("creates dashed edge between parent and revised hypothesis", () => {
    const hyps = [
      makeHypothesis({ id: "h1", status: "refuted" }),
      makeHypothesis({ id: "h2", status: "revised", parentId: "h1" }),
    ];
    const data = buildDiagramData(hyps, [], []);
    expect(data.edges).toHaveLength(1);
    const edge = data.edges[0];
    expect(edge.source).toBe("hyp:h1");
    expect(edge.target).toBe("hyp:h2");
    expect(edge.label).toBe("revised to");
    expect(edge.style?.strokeDasharray).toBe("6 4");
  });

  it("skips edge when parentId references non-existent hypothesis", () => {
    const hyps = [makeHypothesis({ id: "h2", parentId: "h_nonexistent" })];
    const data = buildDiagramData(hyps, [], []);
    expect(data.edges).toHaveLength(0);
  });

  it("creates experiment nodes with edge to hypothesis", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [],
    );
    const nodes = getInvestigationNodes(data);
    expect(nodes).toHaveLength(2);
    expect(data.edges).toHaveLength(1);
    expect(data.edges[0].label).toBe("tested by");
    expect(data.edges[0].type).toBe("smoothstep");
  });

  it("creates finding nodes with evidence-labeled edge", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding()],
    );
    const nodes = getInvestigationNodes(data);
    expect(nodes).toHaveLength(3);
    expect(data.edges).toHaveLength(2);
    const findingEdge = data.edges[data.edges.length - 1];
    expect(findingEdge.label).toBe("supports");
  });

  it("uses contradicting color for contradicting findings", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding({ evidenceType: "contradicting" })],
    );
    const findingEdge = data.edges[data.edges.length - 1];
    expect(findingEdge.style?.stroke).toBe("#ef4444");
    expect(findingEdge.label).toBe("contradicts");
  });

  it("positions hypotheses in a row with correct spacing", () => {
    const hyps = [
      makeHypothesis({ id: "h1" }),
      makeHypothesis({ id: "h2" }),
    ];
    const data = buildDiagramData(hyps, [], []);
    const nodes = getInvestigationNodes(data);
    expect(nodes[1].position.x - nodes[0].position.x).toBe(260 + 50);
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
    const data = buildDiagramData(hyps, exps, finds);
    expect(getInvestigationNodes(data)).toHaveLength(6);
    expect(data.edges).toHaveLength(4);
  });

  it("is deterministic between calls", () => {
    const args: [HypothesisNode[], ExperimentNode[], FindingNode[]] = [
      [makeHypothesis()], [], [],
    ];
    const data1 = buildDiagramData(...args);
    const data2 = buildDiagramData(...args);
    expect(data1.nodes.length).toBe(data2.nodes.length);
    expect(data1.edges.length).toBe(data2.edges.length);
  });

  it("all nodes have required React Flow fields", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding()],
    );
    for (const node of data.nodes) {
      expect(node.id).toBeDefined();
      expect(node.type).toBeDefined();
      expect(node.position).toBeDefined();
      expect(node.data).toBeDefined();
    }
  });

  it("all edges have required React Flow fields", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding()],
    );
    for (const edge of data.edges) {
      expect(edge.id).toBeDefined();
      expect(edge.source).toBeDefined();
      expect(edge.target).toBeDefined();
    }
  });
});

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

describe("buildDiagramData", () => {
  it("returns empty data for no hypotheses", () => {
    const data = buildDiagramData([], [], []);
    expect(data.nodes).toEqual([]);
    expect(data.edges).toEqual([]);
  });

  it("creates root and hypothesis nodes", () => {
    const data = buildDiagramData([makeHypothesis()], [], []);
    const nodes = getInvestigationNodes(data);

    // Should have Root + 1 Hypothesis
    expect(nodes).toHaveLength(2);

    const root = nodes.find(n => n.id === "root-prompt");
    expect(root).toBeDefined();
    expect(root?.data.type).toBe("root");

    const hyp = nodes.find(n => n.id === "tree-h1");
    expect(hyp).toBeDefined();
    expect(hyp?.data.label).toContain("Test hypothesis");
  });

  it("connects root to hypothesis", () => {
    const data = buildDiagramData([makeHypothesis()], [], []);
    const edge = data.edges.find(e => e.source === "root-prompt" && e.target === "tree-h1");
    expect(edge).toBeDefined();
  });

  it("applies correct status colors", () => {
    const data = buildDiagramData(
      [makeHypothesis({ status: "supported" })],
      [],
      [],
    );
    const hyp = data.nodes.find(n => n.id === "tree-h1");
    expect(hyp?.data.stroke).toBeDefined();
    expect(hyp?.data.fill).toBeDefined();
    // Verify it uses the "supported" color (green-ish)
    expect(hyp?.data.stroke).toContain("#22c55e"); // OR check the var usage if updated?
    // In diagram-builder.ts we defined colors: supported: { stroke: "var(--color-secondary)", ... }
    // Wait, I updated status_styles to use vars in step 58 replacement, 
    // BUT in the interface I added in step 81, I didn't verify the values.
    // Let's check the code I wrote in step 58.
    // const STATUS_STYLES = { supported: { stroke: "var(--color-secondary)", ... } }
    // So expecting var string.
    expect(hyp?.data.stroke).toBe("var(--color-secondary)");
  });

  it("creates experiment nodes connected to hypothesis", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [],
    );
    const exp = data.nodes.find(n => n.id === "tree-e1");
    expect(exp).toBeDefined();
    expect(exp?.data.type).toBe("experiment");

    const edge = data.edges.find(e => e.source === "tree-h1" && e.target === "tree-e1");
    expect(edge).toBeDefined();
    expect(edge?.label).toBe("tested by");
  });

  it("creates finding nodes connected to experiment", () => {
    const data = buildDiagramData(
      [makeHypothesis()],
      [makeExperiment()],
      [makeFinding({ source_id: "e1" })], // Ensure source_id linkage
    );
    const finding = data.nodes.find(n => n.id === "tree-f1");
    expect(finding).toBeDefined();
    expect(finding?.data.type).toBe("finding");

    const edge = data.edges.find(e => e.source === "tree-e1" && e.target === "tree-f1");
    expect(edge).toBeDefined();
    expect(edge?.sourceHandle).toBe("right");
    expect(edge?.targetHandle).toBe("left");
  });

  it("handles revision hierarchy (hypothesis -> experiment -> hypothesis)", () => {
    const h1 = makeHypothesis({ id: "h1" });
    const e1 = makeExperiment({ id: "e1", hypothesisId: "h1" });
    const h2 = makeHypothesis({ id: "h2", parentId: "h1", status: "revised" });

    // Logic: h2 is child of h1? No, my logic says h2 is child of EXPERIMENT e1 testing h1?
    // Let's check diagram-builder.ts logic for 'experiment' children:
    // const revisions = hypotheses.filter(h => h.parentId === data.hypothesisId);
    // So if h2.parentId === h1.id (which is e1.hypothesisId), then h2 is child of e1.

    const data = buildDiagramData([h1, h2], [e1], []);

    // Check edge e1 -> h2
    const edge = data.edges.find(e => e.source === "tree-e1" && e.target === "tree-h2");
    expect(edge).toBeDefined();
    expect(edge?.label).toBe("led to revision");
  });

  it("calculates positions (basic check)", () => {
    const data = buildDiagramData([makeHypothesis()], [], []);
    const root = data.nodes.find(n => n.id === "root-prompt");
    const hyp = data.nodes.find(n => n.id === "tree-h1");

    // Root at level 0, Hyp at level 1 (y + 50)
    // Level height 200.
    // Root y: 0 * 200 + 50 = 50.
    // Hyp y: 1 * 200 + 50 = 250.
    expect(root?.position.y).toBe(50);
    expect(hyp?.position.y).toBe(250);
  });
});

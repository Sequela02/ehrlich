import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { InvestigationDiagram } from "./InvestigationDiagram";
import type { HypothesisNode, ExperimentNode, FindingNode } from "../lib/diagram-builder";

vi.mock("@xyflow/react", () => ({
  ReactFlow: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="reactflow">{children}</div>
  ),
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Background: () => null,
  Controls: () => null,
  MiniMap: () => null,
  Handle: () => null,
  Position: { Top: "top", Bottom: "bottom" },
}));

vi.mock("./DiagramRenderer", () => ({
  DiagramRenderer: () => <div data-testid="diagram-renderer" />,
}));

afterEach(() => {
  cleanup();
});

const hypothesis: HypothesisNode = {
  id: "h1",
  statement: "Test hypothesis",
  status: "supported",
};

const experiment: ExperimentNode = {
  id: "e1",
  hypothesisId: "h1",
  description: "Test experiment",
  status: "completed",
};

const finding: FindingNode = {
  id: "f1",
  hypothesisId: "h1",
  summary: "Test finding",
  evidenceType: "supporting",
};

describe("InvestigationDiagram", () => {
  it("shows empty state when no hypotheses", () => {
    render(
      <InvestigationDiagram
        hypotheses={[]}
        experiments={[]}
        findings={[]}
      />,
    );
    expect(screen.getByText(/no hypotheses to diagram/i)).toBeInTheDocument();
  });

  it("renders diagram when hypotheses exist", async () => {
    render(
      <InvestigationDiagram
        hypotheses={[hypothesis]}
        experiments={[experiment]}
        findings={[finding]}
      />,
    );
    const renderer = await screen.findByTestId("diagram-renderer");
    expect(renderer).toBeInTheDocument();
  });
});

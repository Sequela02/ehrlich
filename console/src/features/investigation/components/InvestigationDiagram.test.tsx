import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { InvestigationDiagram } from "./InvestigationDiagram";
import type { HypothesisNode, ExperimentNode, FindingNode } from "../lib/diagram-builder";

vi.mock("./ExcalidrawWrapper", () => ({
  default: ({ viewMode }: { viewMode: boolean }) => (
    <div data-testid="excalidraw-wrapper" data-view-mode={String(viewMode)}>
      Excalidraw Mock
    </div>
  ),
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
        completed={false}
      />,
    );
    expect(screen.getByText(/no hypotheses to diagram/i)).toBeInTheDocument();
  });

  it("renders ExcalidrawWrapper when hypotheses exist", async () => {
    render(
      <InvestigationDiagram
        hypotheses={[hypothesis]}
        experiments={[experiment]}
        findings={[finding]}
        completed={false}
      />,
    );
    const wrappers = await screen.findAllByTestId("excalidraw-wrapper");
    expect(wrappers.length).toBeGreaterThanOrEqual(1);
  });

  it("passes viewMode=true when not completed", async () => {
    render(
      <InvestigationDiagram
        hypotheses={[hypothesis]}
        experiments={[]}
        findings={[]}
        completed={false}
      />,
    );
    const wrappers = await screen.findAllByTestId("excalidraw-wrapper");
    expect(wrappers[0].dataset.viewMode).toBe("true");
  });

  it("passes viewMode=false when completed", async () => {
    render(
      <InvestigationDiagram
        hypotheses={[hypothesis]}
        experiments={[]}
        findings={[]}
        completed={true}
      />,
    );
    const wrappers = await screen.findAllByTestId("excalidraw-wrapper");
    expect(wrappers[0].dataset.viewMode).toBe("false");
  });
});

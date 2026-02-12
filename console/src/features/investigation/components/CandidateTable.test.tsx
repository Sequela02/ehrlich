import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CandidateTable } from "./CandidateTable";

describe("CandidateTable", () => {
  it("renders nothing when no candidates", () => {
    const { container } = render(<CandidateTable candidates={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders candidate rows with structure thumbnails", () => {
    render(
      <CandidateTable
        candidates={[
          { identifier: "CCO", identifier_type: "smiles", name: "Ethanol", rank: 1, notes: "Top candidate", scores: {}, attributes: {} },
          { identifier: "c1ccccc1", identifier_type: "smiles", name: "Benzene", rank: 2, notes: "", scores: {}, attributes: {} },
        ]}
      />,
    );
    expect(screen.getByText("Ranked Candidates")).toBeInTheDocument();
    expect(screen.getByText("Ethanol")).toBeInTheDocument();
    expect(screen.getByText("Top candidate")).toBeInTheDocument();

    // SMILES are now in img alt text, not raw text
    const ethanol = screen.getByAltText("CCO");
    expect(ethanol).toBeInTheDocument();
    expect(ethanol.tagName).toBe("IMG");

    const benzene = screen.getByAltText("c1ccccc1");
    expect(benzene).toBeInTheDocument();
  });

  it("renders structure column header", () => {
    render(
      <CandidateTable
        candidates={[{ identifier: "CCO", identifier_type: "smiles", name: "Ethanol", rank: 1, notes: "", scores: {}, attributes: {} }]}
      />,
    );
    expect(screen.getAllByText("Structure").length).toBeGreaterThanOrEqual(1);
  });
});

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CandidateTable } from "./CandidateTable";

describe("CandidateTable", () => {
  it("renders nothing when no candidates", () => {
    const { container } = render(<CandidateTable candidates={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders candidate rows", () => {
    render(
      <CandidateTable
        candidates={[
          { smiles: "CCO", name: "Ethanol", rank: 1, notes: "Top candidate" },
          { smiles: "c1ccccc1", name: "Benzene", rank: 2, notes: "" },
        ]}
      />,
    );
    expect(screen.getByText("Ranked Candidates")).toBeInTheDocument();
    expect(screen.getByText("Ethanol")).toBeInTheDocument();
    expect(screen.getByText("CCO")).toBeInTheDocument();
    expect(screen.getByText("Top candidate")).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FindingsPanel } from "./FindingsPanel";

describe("FindingsPanel", () => {
  it("shows empty state when no findings", () => {
    render(<FindingsPanel findings={[]} />);
    expect(screen.getByText(/findings will appear/i)).toBeInTheDocument();
  });

  it("renders findings with count", () => {
    render(
      <FindingsPanel
        findings={[
          { title: "Key discovery", detail: "Important detail", phase: "Literature Review" },
          { title: "Second finding", detail: "More detail", phase: "Data Exploration" },
        ]}
      />,
    );
    expect(screen.getByText("Findings (2)")).toBeInTheDocument();
    expect(screen.getByText("Key discovery")).toBeInTheDocument();
    expect(screen.getByText("Second finding")).toBeInTheDocument();
    expect(screen.getByText("Literature Review")).toBeInTheDocument();
  });

  it("shows full detail text without truncation", () => {
    const longDetail = "A".repeat(300);
    render(
      <FindingsPanel findings={[{ title: "Long", detail: longDetail, phase: "" }]} />,
    );
    expect(screen.getByText(longDetail)).toBeInTheDocument();
  });
});

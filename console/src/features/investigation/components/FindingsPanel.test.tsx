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
          { title: "Key discovery", detail: "Important detail", hypothesis_id: "h1", evidence_type: "supporting" },
          { title: "Second finding", detail: "More detail", hypothesis_id: "h2", evidence_type: "contradicting" },
        ]}
      />,
    );
    expect(screen.getByText("Findings (2)")).toBeInTheDocument();
    expect(screen.getByText("Key discovery")).toBeInTheDocument();
    expect(screen.getByText("Second finding")).toBeInTheDocument();
    expect(screen.getByText("supporting")).toBeInTheDocument();
    expect(screen.getByText("contradicting")).toBeInTheDocument();
  });

  it("shows full detail text without truncation", () => {
    const longDetail = "A".repeat(300);
    render(
      <FindingsPanel findings={[{ title: "Long", detail: longDetail, hypothesis_id: "", evidence_type: "neutral" }]} />,
    );
    expect(screen.getByText(longDetail)).toBeInTheDocument();
  });
});

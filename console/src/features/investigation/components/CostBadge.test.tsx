import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CostBadge } from "./CostBadge";

describe("CostBadge", () => {
  it("renders nothing when cost is null", () => {
    const { container } = render(<CostBadge cost={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders cost info", () => {
    render(
      <CostBadge
        cost={{
          inputTokens: 1500,
          outputTokens: 500,
          totalTokens: 2000,
          totalCost: 0.0121,
          toolCalls: 5,
        }}
      />,
    );
    expect(screen.getByText("1,500 in")).toBeInTheDocument();
    expect(screen.getByText("500 out")).toBeInTheDocument();
    expect(screen.getByText("5 tools")).toBeInTheDocument();
    expect(screen.getByText("$0.0121")).toBeInTheDocument();
  });
});

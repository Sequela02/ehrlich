import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TemplateCards } from "./TemplateCards";

describe("TemplateCards", () => {
  it("renders 4 template cards with domain labels", () => {
    render(<TemplateCards onSelect={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(4);
  });

  it("renders all 4 template domains", () => {
    render(<TemplateCards onSelect={() => {}} />);
    const domains = [
      "Antimicrobial Resistance",
      "Neurodegenerative Disease",
      "Environmental Science",
      "Oncology",
    ];
    for (const domain of domains) {
      expect(screen.getAllByText(domain).length).toBeGreaterThanOrEqual(1);
    }
  });
});

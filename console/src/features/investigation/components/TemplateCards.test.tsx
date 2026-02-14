import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TemplateCards } from "./TemplateCards";

describe("TemplateCards", () => {
  it("renders 9 template cards with domain labels", () => {
    render(<TemplateCards onSelect={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(9);
  });

  it("renders all template domains", () => {
    render(<TemplateCards onSelect={() => {}} />);
    const domains = [
      "Antimicrobial Resistance",
      "Neurodegenerative Disease",
      "Environmental Science",
      "Oncology",
      "Exercise Physiology",
      "Sports Medicine",
      "Sports Nutrition",
      "Education Policy",
      "Health Policy",
    ];
    for (const domain of domains) {
      expect(screen.getAllByText(domain).length).toBeGreaterThanOrEqual(1);
    }
  });
});

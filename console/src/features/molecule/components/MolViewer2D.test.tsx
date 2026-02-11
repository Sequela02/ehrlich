import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "vitest";
import { MolViewer2D } from "./MolViewer2D";

afterEach(cleanup);

describe("MolViewer2D", () => {
  it("renders img with correct src", () => {
    render(<MolViewer2D smiles="CCO" />);
    const img = screen.getByAltText("CCO");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", expect.stringContaining("/api/v1/molecule/depict"));
  });

  it("encodes special characters in SMILES", () => {
    render(<MolViewer2D smiles="CC(=O)Oc1ccccc1C(=O)O" />);
    const img = screen.getByAltText("CC(=O)Oc1ccccc1C(=O)O");
    const src = img.getAttribute("src") ?? "";
    expect(src).toContain("smiles=CC");
    expect(src).toContain("%3DO");
  });

  it("passes custom dimensions", () => {
    render(<MolViewer2D smiles="CCO" width={100} height={80} />);
    const img = screen.getByAltText("CCO");
    const src = img.getAttribute("src") ?? "";
    expect(src).toContain("w=100");
    expect(src).toContain("h=80");
  });

  it("shows SMILES text on image error", () => {
    render(<MolViewer2D smiles="CCO" />);
    const img = screen.getByAltText("CCO");
    fireEvent.error(img);
    expect(screen.getByText("CCO")).toBeInTheDocument();
  });
});

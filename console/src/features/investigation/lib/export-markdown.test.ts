import { describe, it, expect } from "vitest";
import { generateMarkdown, type ExportData } from "./export-markdown";

const BASE_DATA: ExportData = {
  prompt: "Find MRSA antimicrobials",
  summary: "We identified 3 candidates.",
  hypotheses: [
    {
      id: "h1",
      statement: "Compound X inhibits PBP2a",
      rationale: "Based on structural analysis",
      status: "supported",
      parent_id: "",
      confidence: 0.85,
      supporting_evidence: [],
      contradicting_evidence: [],
    },
  ],
  experiments: [
    {
      id: "e1",
      hypothesis_id: "h1",
      description: "Dock compounds against PBP2a",
      status: "completed",
      tool_count: 5,
      finding_count: 2,
    },
  ],
  findings: [
    {
      title: "Strong binding affinity",
      detail: "Docking score -9.2 kcal/mol",
      hypothesis_id: "h1",
      evidence_type: "supporting",
      source_type: "pdb",
      source_id: "2ABC",
    },
  ],
  candidates: [
    {
      smiles: "CC(=O)Oc1ccccc1C(=O)O",
      name: "Aspirin",
      rank: 1,
      notes: "Top candidate",
      prediction_score: 0.92,
      docking_score: -9.2,
      admet_score: 0.88,
      resistance_risk: "low",
    },
  ],
  negativeControls: [
    {
      smiles: "CCO",
      name: "Ethanol",
      prediction_score: 0.05,
      correctly_classified: true,
      source: "manual",
    },
  ],
  cost: {
    inputTokens: 50000,
    outputTokens: 10000,
    totalTokens: 60000,
    totalCost: 1.2345,
    toolCalls: 15,
  },
};

describe("generateMarkdown", () => {
  it("includes all 8 sections", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("## Research Question");
    expect(md).toContain("## Executive Summary");
    expect(md).toContain("## Hypotheses & Outcomes");
    expect(md).toContain("## Methodology");
    expect(md).toContain("## Key Findings");
    expect(md).toContain("## Candidate Molecules");
    expect(md).toContain("## Model Validation");
    expect(md).toContain("## Cost & Performance");
  });

  it("includes research prompt as blockquote", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("> Find MRSA antimicrobials");
  });

  it("includes hypothesis table with status and confidence", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("| supported | 85% | Compound X inhibits PBP2a |");
  });

  it("includes candidate table with scores", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("| 1 | Aspirin |");
    expect(md).toContain("0.92");
    expect(md).toContain("-9.2");
  });

  it("includes finding with source provenance", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("[pdb: 2ABC]");
  });

  it("includes negative control validation", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("1/1 correct");
    expect(md).toContain("| Ethanol |");
  });

  it("includes cost breakdown", () => {
    const md = generateMarkdown(BASE_DATA);
    expect(md).toContain("$1.2345");
    expect(md).toContain("15");
  });

  it("handles empty data gracefully", () => {
    const md = generateMarkdown({
      prompt: "",
      summary: "",
      hypotheses: [],
      experiments: [],
      findings: [],
      candidates: [],
      negativeControls: [],
      cost: null,
    });
    expect(md).toContain("# Investigation Report");
    expect(md).not.toContain("## Research Question");
    expect(md).not.toContain("## Candidate Molecules");
  });
});

import { describe, it, expect } from "vitest";
import { parseHypothesisStatement } from "./parse-hypothesis";

describe("parseHypothesisStatement", () => {
  describe("SMILES extraction", () => {
    it("extracts SMILES from standard (SMILES: ...) notation", () => {
      const result = parseHypothesisStatement(
        "Huperzine A (SMILES: C=C[C@H]1C[C@@H]2CC3=CC(=O)C=C[C@@]3(N2C1)C) will demonstrate activity",
      );
      expect(result.smiles).toBe(
        "C=C[C@H]1C[C@@H]2CC3=CC(=O)C=C[C@@]3(N2C1)C",
      );
      expect(result.compoundName).toBe("Huperzine A");
    });

    it("handles SMILES with balanced internal parentheses", () => {
      const result = parseHypothesisStatement(
        "Aspirin (SMILES: CC(=O)Oc1ccccc1C(=O)O) is well-known",
      );
      expect(result.smiles).toBe("CC(=O)Oc1ccccc1C(=O)O");
    });

    it("returns null smiles when no SMILES marker present", () => {
      const result = parseHypothesisStatement(
        "Compounds with thiazolidine rings will show activity",
      );
      expect(result.smiles).toBeNull();
      expect(result.compoundName).toBeNull();
      expect(result.cleanedStatement).toBe(
        "Compounds with thiazolidine rings will show activity",
      );
    });

    it("handles case-insensitive SMILES marker", () => {
      const result = parseHypothesisStatement(
        "Ethanol (smiles: CCO) is simple",
      );
      expect(result.smiles).toBe("CCO");
    });

    it("handles empty SMILES block gracefully", () => {
      const result = parseHypothesisStatement(
        "Compound (SMILES: ) has no structure",
      );
      expect(result.smiles).toBeNull();
    });

    it("extracts first SMILES when multiple present", () => {
      const result = parseHypothesisStatement(
        "Drug A (SMILES: CCO) compared to Drug B (SMILES: CC(=O)O)",
      );
      expect(result.smiles).toBe("CCO");
    });
  });

  describe("compound name extraction", () => {
    it("extracts compound name before SMILES", () => {
      const result = parseHypothesisStatement(
        "6-Aminopenicillanic acid (SMILES: CC1(C)SC2CC(=O)N2C1C(=O)O) is a core structure",
      );
      expect(result.compoundName).toBe("6-Aminopenicillanic acid");
    });

    it("handles multi-word compound names", () => {
      const result = parseHypothesisStatement(
        "Galantamine hydrobromide (SMILES: CN1CCC2=CC(=O)OC1) should work",
      );
      expect(result.compoundName).toBe("Galantamine hydrobromide");
    });

    it("returns null when name segment is a stop word", () => {
      const result = parseHypothesisStatement(
        "the (SMILES: CCO) compound is active",
      );
      expect(result.compoundName).toBeNull();
    });

    it("extracts name after comma-separated clause", () => {
      const result = parseHypothesisStatement(
        "A natural product, Berberine (SMILES: COc1ccc2CC3) will inhibit",
      );
      expect(result.compoundName).toBe("Berberine");
    });
  });

  describe("cleaned statement", () => {
    it("removes SMILES block from statement", () => {
      const result = parseHypothesisStatement(
        "Huperzine A (SMILES: C=C[C@H]1CC) will demonstrate activity",
      );
      expect(result.cleanedStatement).toBe(
        "Huperzine A will demonstrate activity",
      );
      expect(result.cleanedStatement).not.toContain("SMILES");
    });

    it("preserves original statement when no SMILES", () => {
      const original = "Generic hypothesis about compounds";
      const result = parseHypothesisStatement(original);
      expect(result.cleanedStatement).toBe(original);
    });

    it("cleans up double commas from removal", () => {
      const result = parseHypothesisStatement(
        "Test (SMILES: CCO), a compound, will work",
      );
      expect(result.cleanedStatement).not.toContain(",,");
    });
  });

  describe("prediction extraction", () => {
    it("extracts IC50 prediction", () => {
      const result = parseHypothesisStatement(
        "The compound will show IC50 < 1 μM against the target",
      );
      expect(result.predictions).toContainEqual({
        label: "IC50",
        value: "< 1 μM",
      });
    });

    it("extracts multiple predictions", () => {
      const result = parseHypothesisStatement(
        "Drug with logP 1-3, MW < 500, PSA < 90 Å²",
      );
      expect(result.predictions.length).toBeGreaterThanOrEqual(3);
      expect(result.predictions.find((p) => p.label === "logP")).toBeDefined();
      expect(result.predictions.find((p) => p.label === "MW")).toBeDefined();
      expect(result.predictions.find((p) => p.label === "PSA")).toBeDefined();
    });

    it("returns empty array when no predictions found", () => {
      const result = parseHypothesisStatement(
        "The compound class will show activity",
      );
      expect(result.predictions).toEqual([]);
    });

    it("deduplicates predictions by label", () => {
      const result = parseHypothesisStatement(
        "IC50 < 1 μM and IC50 > 0.1 nM",
      );
      const ic50s = result.predictions.filter((p) => p.label === "IC50");
      expect(ic50s).toHaveLength(1);
    });

    it("works alongside SMILES extraction", () => {
      const result = parseHypothesisStatement(
        "Huperzine A (SMILES: CCO) has IC50 < 1 μM and logP 1-3",
      );
      expect(result.smiles).toBe("CCO");
      expect(result.predictions.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("full statement parsing", () => {
    it("parses real-world hypothesis statement", () => {
      const statement =
        'Huperzine A (SMILES: C=C[C@H]1C[C@@H]2CC3=CC(=O)C=C[C@@]3(N2C1)C), a Lycopodium alkaloid confirmed in Lycopodiaceae species including L. selago, will demonstrate potent acetylcholinesterase inhibition (IC50 < 1 μM) and favorable predicted CNS penetration (logP 1-3, MW < 500, PSA < 90 Å²).';

      const result = parseHypothesisStatement(statement);

      expect(result.smiles).toBe(
        "C=C[C@H]1C[C@@H]2CC3=CC(=O)C=C[C@@]3(N2C1)C",
      );
      expect(result.compoundName).toBe("Huperzine A");
      expect(result.cleanedStatement).not.toContain("SMILES:");
      expect(result.cleanedStatement).toContain("Huperzine A");
      expect(result.cleanedStatement).toContain("acetylcholinesterase");
      expect(result.predictions.length).toBeGreaterThanOrEqual(3);
    });
  });
});

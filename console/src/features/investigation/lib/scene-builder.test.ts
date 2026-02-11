import { describe, it, expect } from "vitest";
import { buildSceneUpdates } from "./scene-builder";

describe("buildSceneUpdates", () => {
  describe("tool_called events", () => {
    it("dock_against_target adds protein and ligand", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: {
          tool_name: "dock_against_target",
          tool_input: { pdb_id: "1VQQ", smiles: "CCO" },
        },
      });
      expect(actions).toHaveLength(2);
      expect(actions[0]).toEqual({
        type: "addProtein",
        pdbId: "1VQQ",
        style: "cartoon",
      });
      expect(actions[1]).toEqual({
        type: "addLigand",
        smiles: "CCO",
        style: "stick",
        color: "#22c55e",
      });
    });

    it("dock_against_target with only pdb_id adds protein only", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: {
          tool_name: "dock_against_target",
          tool_input: { pdb_id: "2XCT" },
        },
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe("addProtein");
    });

    it("dock_against_target with no inputs returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "dock_against_target", tool_input: {} },
      });
      expect(actions).toHaveLength(0);
    });

    it("tanimoto_similarity adds two ligands with different colors", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: {
          tool_name: "tanimoto_similarity",
          tool_input: { smiles_a: "CCO", smiles_b: "CC(=O)O" },
        },
      });
      expect(actions).toHaveLength(2);
      expect(actions[0]).toEqual({
        type: "addLigand",
        smiles: "CCO",
        style: "stick",
        color: "#a78bfa",
      });
      expect(actions[1]).toEqual({
        type: "addLigand",
        smiles: "CC(=O)O",
        style: "stick",
        color: "#22d3ee",
      });
    });

    it("tanimoto_similarity with only smiles_a adds one ligand", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: {
          tool_name: "tanimoto_similarity",
          tool_input: { smiles_a: "CCO" },
        },
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe("addLigand");
    });

    it.each([
      "validate_smiles",
      "compute_descriptors",
      "compute_fingerprint",
      "generate_3d",
      "substructure_match",
      "predict_admet",
    ])("%s with smiles adds ligand", (toolName) => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: toolName, tool_input: { smiles: "c1ccccc1" } },
      });
      expect(actions).toHaveLength(1);
      expect(actions[0]).toEqual({
        type: "addLigand",
        smiles: "c1ccccc1",
        style: "stick",
      });
    });

    it.each([
      "validate_smiles",
      "compute_descriptors",
    ])("%s without smiles returns empty", (toolName) => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: toolName, tool_input: {} },
      });
      expect(actions).toHaveLength(0);
    });

    it("search_protein_targets returns empty on tool_called", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "search_protein_targets", tool_input: {} },
      });
      expect(actions).toEqual([]);
    });

    it("predict_candidates returns empty on tool_called", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "predict_candidates", tool_input: {} },
      });
      expect(actions).toEqual([]);
    });

    it("unknown tool without smiles returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "search_literature", tool_input: { query: "test" } },
      });
      expect(actions).toEqual([]);
    });
  });

  describe("tool_result events", () => {
    it("dock_against_target with good score adds green label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "dock_against_target",
          result_preview: "Docking score: -8.5 kcal/mol",
        },
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe("addLabel");
      if (actions[0].type === "addLabel") {
        expect(actions[0].text).toBe("-8.5 kcal/mol");
        expect(actions[0].color).toBe("#22c55e");
      }
    });

    it("dock_against_target with moderate score adds orange label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "dock_against_target",
          result_preview: "score: -6.0",
        },
      });
      expect(actions).toHaveLength(1);
      if (actions[0].type === "addLabel") {
        expect(actions[0].color).toBe("#f97316");
      }
    });

    it("dock_against_target with poor score adds red label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "dock_against_target",
          result_preview: "score: -3.2",
        },
      });
      expect(actions).toHaveLength(1);
      if (actions[0].type === "addLabel") {
        expect(actions[0].color).toBe("#ef4444");
      }
    });

    it("dock_against_target with no score returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "dock_against_target",
          result_preview: "Docking completed",
        },
      });
      expect(actions).toEqual([]);
    });

    it("generate_3d with energy adds label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "generate_3d",
          result_preview: '{"mol_block": "...", "energy": -45.23, "num_atoms": 12}',
        },
      });
      expect(actions).toHaveLength(1);
      if (actions[0].type === "addLabel") {
        expect(actions[0].text).toBe("E = -45.2 kcal/mol");
        expect(actions[0].color).toBe("#a78bfa");
      }
    });

    it("generate_3d with no energy returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "generate_3d",
          result_preview: "Generation failed",
        },
      });
      expect(actions).toEqual([]);
    });

    it("compute_descriptors with properties adds label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "compute_descriptors",
          result_preview: '{"molecular_weight": 180.16, "logp": -0.32, "qed": 0.74, "tpsa": 63.6}',
        },
      });
      expect(actions).toHaveLength(1);
      if (actions[0].type === "addLabel") {
        expect(actions[0].text).toContain("MW 180");
        expect(actions[0].text).toContain("LogP -0.3");
        expect(actions[0].text).toContain("QED 0.74");
        expect(actions[0].color).toBe("#94a3b8");
      }
    });

    it("compute_descriptors with partial properties adds label", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "compute_descriptors",
          result_preview: '{"molecular_weight": 342.3}',
        },
      });
      expect(actions).toHaveLength(1);
      if (actions[0].type === "addLabel") {
        expect(actions[0].text).toBe("MW 342");
      }
    });

    it("compute_descriptors with no matching properties returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "compute_descriptors",
          result_preview: "Error computing descriptors",
        },
      });
      expect(actions).toEqual([]);
    });

    it("search_compounds extracts SMILES as ligands", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "search_compounds",
          result_preview: '[{"smiles": "CCO", "name": "ethanol"}, {"smiles": "CC(=O)O", "name": "acetic acid"}]',
        },
      });
      expect(actions).toHaveLength(2);
      expect(actions[0]).toEqual({
        type: "addLigand",
        smiles: "CCO",
        style: "stick",
        color: "#38bdf8",
      });
      expect(actions[1]).toEqual({
        type: "addLigand",
        smiles: "CC(=O)O",
        style: "stick",
        color: "#38bdf8",
      });
    });

    it("search_compounds limits to 5 results", () => {
      const entries = Array.from({ length: 8 }, (_, i) => `{"smiles": "C${i}"}`);
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "search_compounds",
          result_preview: `[${entries.join(", ")}]`,
        },
      });
      expect(actions).toHaveLength(5);
    });

    it("search_compounds with no SMILES returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "search_compounds",
          result_preview: "No compounds found",
        },
      });
      expect(actions).toEqual([]);
    });

    it("predict_candidates with scores returns colorByScore", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "predict_candidates",
          result_preview: 'SMILES: CCO score: 0.85, SMILES: CC(=O)O score: 0.42',
        },
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe("colorByScore");
      if (actions[0].type === "colorByScore") {
        expect(actions[0].scores).toHaveLength(2);
        expect(actions[0].scores[0].smiles).toBe("CCO");
        expect(actions[0].scores[0].score).toBe(0.85);
      }
    });

    it("predict_candidates with no scores returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "predict_candidates",
          result_preview: "No candidates found",
        },
      });
      expect(actions).toEqual([]);
    });

    it("search_protein_targets with PDB IDs returns addProtein actions", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "search_protein_targets",
          result_preview: 'pdb_id: "1VQQ", pdb_id: "2XCT", pdb_id: "1AD4", pdb_id: "3SPU"',
        },
      });
      expect(actions).toHaveLength(3);
      expect(actions.every((a) => a.type === "addProtein")).toBe(true);
      if (actions[0].type === "addProtein") {
        expect(actions[0].pdbId).toBe("1VQQ");
      }
    });

    it("search_protein_targets with no PDB IDs returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_result",
        data: {
          tool_name: "search_protein_targets",
          result_preview: "No targets found",
        },
      });
      expect(actions).toEqual([]);
    });
  });

  describe("completed event", () => {
    it("highlights top 3 candidates and zooms", () => {
      const actions = buildSceneUpdates({
        type: "completed",
        data: {
          candidates: [
            { smiles: "CCO" },
            { smiles: "CC(=O)O" },
            { smiles: "c1ccccc1" },
            { smiles: "CC" },
          ],
        },
      });
      expect(actions).toHaveLength(4);
      expect(actions[0]).toEqual({ type: "highlight", smiles: "CCO", color: "#22c55e" });
      expect(actions[1]).toEqual({ type: "highlight", smiles: "CC(=O)O", color: "#22c55e" });
      expect(actions[2]).toEqual({ type: "highlight", smiles: "c1ccccc1", color: "#22c55e" });
      expect(actions[3]).toEqual({ type: "zoomTo" });
    });

    it("completed with no candidates returns empty", () => {
      const actions = buildSceneUpdates({
        type: "completed",
        data: { candidates: [] },
      });
      expect(actions).toEqual([]);
    });

    it("completed with missing candidates field returns empty", () => {
      const actions = buildSceneUpdates({
        type: "completed",
        data: {},
      });
      expect(actions).toEqual([]);
    });
  });

  describe("unknown events", () => {
    it("thinking event returns empty", () => {
      const actions = buildSceneUpdates({
        type: "thinking",
        data: { text: "Analyzing..." },
      });
      expect(actions).toEqual([]);
    });

    it("finding_recorded returns empty", () => {
      const actions = buildSceneUpdates({
        type: "finding_recorded",
        data: { title: "Key finding" },
      });
      expect(actions).toEqual([]);
    });
  });
});

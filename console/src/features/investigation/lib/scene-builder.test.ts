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

    it("search_protein_targets returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "search_protein_targets", tool_input: {} },
      });
      expect(actions).toEqual([]);
    });

    it("predict_candidates returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "predict_candidates", tool_input: {} },
      });
      expect(actions).toEqual([]);
    });

    it("unknown tool returns empty", () => {
      const actions = buildSceneUpdates({
        type: "tool_called",
        data: { tool_name: "validate_smiles", tool_input: {} },
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

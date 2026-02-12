export type SceneAction =
  | { type: "addProtein"; pdbId: string; style: "cartoon" }
  | { type: "addLigand"; smiles: string; molblock?: string; style: "stick"; color?: string }
  | { type: "addLabel"; text: string; position: { x: number; y: number; z: number }; color?: string }
  | { type: "colorByScore"; scores: Array<{ smiles: string; score: number }> }
  | { type: "zoomTo"; selection?: Record<string, unknown> }
  | { type: "highlight"; smiles: string; color: string }
  | { type: "clear" };

interface SSEEventData {
  type: string;
  data: Record<string, unknown>;
}

// Tools that accept a `smiles` input parameter and should trigger molecule display
const SMILES_INPUT_TOOLS = new Set([
  "validate_smiles",
  "compute_descriptors",
  "compute_fingerprint",
  "generate_3d",
  "substructure_match",
  "predict_admet",
]);

/** All tool names that produce molecular 3D data -- used to auto-detect
 *  whether LiveLabViewer should render inside VisualizationPanel. */
export const MOLECULAR_TOOL_NAMES = new Set([
  ...SMILES_INPUT_TOOLS,
  "dock_against_target",
  "tanimoto_similarity",
  "search_compounds",
  "predict_candidates",
  "search_protein_targets",
]);

export function buildSceneUpdates(event: SSEEventData): SceneAction[] {
  const { type, data } = event;

  if (type === "tool_called") {
    const toolName = data.tool_name as string;
    const toolInput = (data.tool_input ?? {}) as Record<string, unknown>;

    if (toolName === "dock_against_target") {
      const actions: SceneAction[] = [];
      const pdbId = toolInput.pdb_id as string | undefined;
      if (pdbId) {
        actions.push({ type: "addProtein", pdbId, style: "cartoon" });
      }
      const smiles = toolInput.smiles as string | undefined;
      if (smiles) {
        actions.push({ type: "addLigand", smiles, style: "stick", color: "#22c55e" });
      }
      return actions;
    }

    if (toolName === "tanimoto_similarity") {
      const actions: SceneAction[] = [];
      const smilesA = toolInput.smiles_a as string | undefined;
      const smilesB = toolInput.smiles_b as string | undefined;
      if (smilesA) actions.push({ type: "addLigand", smiles: smilesA, style: "stick", color: "#a78bfa" });
      if (smilesB) actions.push({ type: "addLigand", smiles: smilesB, style: "stick", color: "#22d3ee" });
      return actions;
    }

    if (SMILES_INPUT_TOOLS.has(toolName)) {
      const smiles = toolInput.smiles as string | undefined;
      if (smiles) {
        return [{ type: "addLigand", smiles, style: "stick" }];
      }
    }

    return [];
  }

  if (type === "tool_result") {
    const toolName = data.tool_name as string;
    const preview = (data.result_preview ?? "") as string;

    if (toolName === "dock_against_target") {
      const scoreMatch = preview.match(/score[:\s]*([-\d.]+)/i);
      if (scoreMatch) {
        const score = parseFloat(scoreMatch[1]);
        return [
          {
            type: "addLabel",
            text: `${score.toFixed(1)} kcal/mol`,
            position: { x: 0, y: 5, z: 0 },
            color: score < -7 ? "#22c55e" : score < -5 ? "#f97316" : "#ef4444",
          },
        ];
      }
    }

    if (toolName === "generate_3d") {
      const energyMatch = preview.match(/"?energy"?\s*:\s*([-\d.]+)/i);
      if (energyMatch) {
        return [{
          type: "addLabel",
          text: `E = ${parseFloat(energyMatch[1]).toFixed(1)} kcal/mol`,
          position: { x: 0, y: 3, z: 0 },
          color: "#a78bfa",
        }];
      }
    }

    if (toolName === "compute_descriptors") {
      const mwMatch = preview.match(/"?molecular_weight"?\s*:\s*([\d.]+)/i);
      const qedMatch = preview.match(/"?qed"?\s*:\s*([\d.]+)/i);
      const logpMatch = preview.match(/"?log_?p"?\s*:\s*([-\d.]+)/i);
      const parts: string[] = [];
      if (mwMatch) parts.push(`MW ${parseFloat(mwMatch[1]).toFixed(0)}`);
      if (logpMatch) parts.push(`LogP ${parseFloat(logpMatch[1]).toFixed(1)}`);
      if (qedMatch) parts.push(`QED ${parseFloat(qedMatch[1]).toFixed(2)}`);
      if (parts.length > 0) {
        return [{
          type: "addLabel",
          text: parts.join(" | "),
          position: { x: 0, y: 3, z: 0 },
          color: "#94a3b8",
        }];
      }
    }

    if (toolName === "search_compounds") {
      const smilesMatches = [...preview.matchAll(/"?smiles"?\s*:\s*"([^"]+)"/gi)];
      return smilesMatches.slice(0, 5).map((m) => ({
        type: "addLigand" as const,
        smiles: m[1],
        style: "stick" as const,
        color: "#38bdf8",
      }));
    }

    if (toolName === "predict_candidates") {
      const scoreMatches = [...preview.matchAll(/(?:smiles|SMILES)[:\s]*([^\s,]+).*?(?:score|prob)[:\s]*([\d.]+)/gi)];
      if (scoreMatches.length > 0) {
        const scores = scoreMatches.map((m) => ({
          smiles: m[1],
          score: parseFloat(m[2]),
        }));
        return [{ type: "colorByScore", scores }];
      }
    }

    if (toolName === "search_protein_targets") {
      const pdbMatches = [...preview.matchAll(/(?:pdb_id|PDB)[:\s]*"?(\w{4})"?/gi)];
      return pdbMatches.slice(0, 3).map((m) => ({
        type: "addProtein" as const,
        pdbId: m[1],
        style: "cartoon" as const,
      }));
    }
  }

  if (type === "completed") {
    const candidates = (data.candidates ?? []) as Array<Record<string, unknown>>;
    const top = candidates.slice(0, 3);
    const actions: SceneAction[] = [];
    for (const c of top) {
      const identifier = (c.identifier ?? c.smiles) as string | undefined;
      if (identifier) {
        actions.push({ type: "highlight", smiles: identifier, color: "#22c55e" });
      }
    }
    if (actions.length > 0) {
      actions.push({ type: "zoomTo" });
    }
    return actions;
  }

  return [];
}

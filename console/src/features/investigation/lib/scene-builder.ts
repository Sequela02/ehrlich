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

    if (toolName === "search_protein_targets") {
      return [];
    }

    if (toolName === "predict_candidates") {
      return [];
    }
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
      const smiles = c.smiles as string | undefined;
      if (smiles) {
        actions.push({ type: "highlight", smiles, color: "#22c55e" });
      }
    }
    if (actions.length > 0) {
      actions.push({ type: "zoomTo" });
    }
    return actions;
  }

  return [];
}

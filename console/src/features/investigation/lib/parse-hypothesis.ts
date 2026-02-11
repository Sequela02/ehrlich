export interface Prediction {
  label: string;
  value: string;
}

export interface ParsedHypothesis {
  compoundName: string | null;
  smiles: string | null;
  cleanedStatement: string;
  predictions: Prediction[];
}

function extractSmilesBlock(
  statement: string,
): { smiles: string; start: number; end: number } | null {
  const marker = statement.toLowerCase().indexOf("(smiles:");
  if (marker === -1) return null;

  let depth = 0;
  let endIdx = -1;
  for (let i = marker; i < statement.length; i++) {
    if (statement[i] === "(") depth++;
    else if (statement[i] === ")") {
      depth--;
      if (depth === 0) {
        endIdx = i;
        break;
      }
    }
  }

  if (endIdx === -1) return null;

  const colonIdx = statement.indexOf(":", marker + 1);
  const smiles = statement.slice(colonIdx + 1, endIdx).trim();

  if (smiles.length === 0) return null;

  return { smiles, start: marker, end: endIdx + 1 };
}

const STOP_WORDS = new Set([
  "a", "an", "the", "of", "in", "for", "with", "and", "or", "to",
  "as", "from", "is", "will", "that", "which", "has", "have", "its",
  "this", "these", "those", "be", "been", "being", "are", "was", "were",
]);

function extractCompoundName(
  statement: string,
  smilesStart: number,
): string | null {
  const before = statement.slice(0, smilesStart).trimEnd();
  if (!before) return null;

  const segments = before.split(/[,;]\s*/);
  let nameSegment = segments[segments.length - 1].trim();

  nameSegment = nameSegment
    .replace(/^(the compound|specifically|namely|i\.e\.|e\.g\.)\s+/i, "")
    .trim();

  const words = nameSegment.split(/\s+/);
  const nameWords: string[] = [];
  for (let i = words.length - 1; i >= 0; i--) {
    const w = words[i];
    // Only treat lowercase words as stop words -- uppercase "A" in
    // "Huperzine A" is part of the compound name, not the article "a"
    if (w === w.toLowerCase() && STOP_WORDS.has(w)) break;
    nameWords.unshift(w);
  }

  const name = nameWords.join(" ").trim();
  if (name.length === 0 || name.length > 80) return null;
  if (!/^[A-Z0-9(βαγδΔ\[(-]/.test(name)) return null;

  return name;
}

const LABEL_MAP: Record<string, string> = {
  ic50: "IC50",
  ec50: "EC50",
  ki: "Ki",
  kd: "Kd",
  mic: "MIC",
  logp: "logP",
  mw: "MW",
  psa: "PSA",
  tpsa: "TPSA",
  qed: "QED",
  hbd: "HBD",
  hba: "HBA",
};

function normalizeLabel(raw: string): string {
  const key = raw.replace(/\s+/g, "").toLowerCase();
  return LABEL_MAP[key] ?? raw;
}

function extractPredictions(statement: string): Prediction[] {
  const pattern =
    /(IC50|EC50|Ki|Kd|MIC|log\s*P|LogP|logP|MW|PSA|TPSA|QED|HBD|HBA)\s*([<>≤≥~=]?\s*[\d.]+(?:\s*[-–]\s*[\d.]+)?(?:\s*[μunp]?[MgmL/²Åå]+(?:\/m[Ll])?)?)/gi;

  const predictions: Prediction[] = [];
  const seen = new Set<string>();
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(statement)) !== null) {
    const label = normalizeLabel(match[1]);
    const value = match[2].trim();
    if (!seen.has(label) && value) {
      seen.add(label);
      predictions.push({ label, value });
    }
  }

  return predictions;
}

export function parseHypothesisStatement(
  statement: string,
): ParsedHypothesis {
  const block = extractSmilesBlock(statement);

  if (!block) {
    return {
      compoundName: null,
      smiles: null,
      cleanedStatement: statement,
      predictions: extractPredictions(statement),
    };
  }

  const compoundName = extractCompoundName(statement, block.start);

  let cleaned = statement.slice(0, block.start) + statement.slice(block.end);
  cleaned = cleaned.replace(/\s{2,}/g, " ").replace(/,\s*,/g, ",").trim();
  cleaned = cleaned.replace(/^,\s*/, "").replace(/\s*,$/, "");

  return {
    compoundName,
    smiles: block.smiles,
    cleanedStatement: cleaned,
    predictions: extractPredictions(statement),
  };
}

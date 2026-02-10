export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface InvestigationRequest {
  prompt: string;
}

export interface InvestigationResponse {
  id: string;
  status: string;
}

export interface Finding {
  title: string;
  detail: string;
  evidence: string;
  phase: string;
  confidence: number;
}

export interface CandidateRow {
  smiles: string;
  name: string;
  predictionScore: number;
  dockingScore: number;
  admetScore: number;
  resistanceRisk: string;
  rank: number;
}

export interface CostInfo {
  inputTokens: number;
  outputTokens: number;
  totalCost: number;
  toolCalls: number;
}

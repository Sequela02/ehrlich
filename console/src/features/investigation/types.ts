export type SSEEventType =
  | "phase_started"
  | "phase_completed"
  | "tool_called"
  | "tool_result"
  | "finding_recorded"
  | "thinking"
  | "error"
  | "completed"
  | "director_planning"
  | "director_decision"
  | "output_summarized";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

export interface PhaseStartedData {
  phase: string;
  investigation_id: string;
}

export interface ToolCalledData {
  tool_name: string;
  tool_input: Record<string, unknown>;
  investigation_id: string;
}

export interface ToolResultData {
  tool_name: string;
  result_preview: string;
  investigation_id: string;
}

export interface FindingRecordedData {
  title: string;
  detail: string;
  phase: string;
  evidence?: string;
  investigation_id: string;
}

export interface ThinkingData {
  text: string;
  investigation_id: string;
}

export interface CompletedData {
  investigation_id: string;
  candidate_count: number;
  summary: string;
  cost: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    tool_calls: number;
    total_cost_usd: number;
  };
  candidates: CandidateRow[];
}

export interface ErrorData {
  error: string;
  investigation_id: string;
}

export interface DirectorPlanningData {
  stage: string;
  phase: string;
  investigation_id: string;
}

export interface DirectorDecisionData {
  stage: string;
  decision: Record<string, unknown>;
  investigation_id: string;
}

export interface OutputSummarizedData {
  tool_name: string;
  original_length: number;
  summarized_length: number;
  investigation_id: string;
}

export interface PhaseCompletedData {
  phase: string;
  tool_count: number;
  finding_count: number;
  investigation_id: string;
}

export interface InvestigationRequest {
  prompt: string;
}

export interface InvestigationResponse {
  id: string;
  status: string;
}

export interface InvestigationSummary {
  id: string;
  prompt: string;
  status: string;
  created_at: string;
  candidate_count: number;
}

export interface Finding {
  title: string;
  detail: string;
  phase: string;
  evidence?: string;
}

export interface CandidateRow {
  smiles: string;
  name: string;
  rank: number;
  notes: string;
  prediction_score?: number;
  docking_score?: number;
  admet_score?: number;
  resistance_risk?: string;
}

export interface ModelCost {
  input_tokens: number;
  output_tokens: number;
  calls: number;
  cost_usd: number;
}

export interface CostInfo {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  totalCost: number;
  toolCalls: number;
  byModel?: Record<string, ModelCost>;
}

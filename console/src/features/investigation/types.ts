export type SSEEventType =
  | "phase_started"
  | "tool_called"
  | "tool_result"
  | "finding_recorded"
  | "thinking"
  | "error"
  | "completed";

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
}

export interface ErrorData {
  error: string;
  investigation_id: string;
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
  phase: string;
}

export interface CandidateRow {
  smiles: string;
  name: string;
  rank: number;
  notes: string;
}

export interface CostInfo {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  totalCost: number;
  toolCalls: number;
}

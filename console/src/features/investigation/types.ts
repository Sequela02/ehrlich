export type SSEEventType =
  | "hypothesis_formulated"
  | "experiment_started"
  | "experiment_completed"
  | "hypothesis_evaluated"
  | "negative_control"
  | "tool_called"
  | "tool_result"
  | "finding_recorded"
  | "thinking"
  | "error"
  | "completed"
  | "output_summarized"
  | "phase_changed"
  | "cost_update"
  | "hypothesis_approval_requested";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

export type HypothesisStatus = "proposed" | "testing" | "supported" | "refuted" | "revised";
export type EvidenceType = "supporting" | "contradicting" | "neutral";

export interface Hypothesis {
  id: string;
  statement: string;
  rationale: string;
  prediction: string;
  null_prediction: string;
  success_criteria: string;
  failure_criteria: string;
  scope: string;
  hypothesis_type: string;
  prior_confidence: number;
  status: HypothesisStatus;
  parent_id: string;
  confidence: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
}

export interface Experiment {
  id: string;
  hypothesis_id: string;
  description: string;
  status: string;
  tool_count?: number;
  finding_count?: number;
}

export interface NegativeControl {
  smiles: string;
  name: string;
  prediction_score: number;
  correctly_classified: boolean;
  source: string;
}

export interface HypothesisFormulatedData {
  hypothesis_id: string;
  statement: string;
  rationale: string;
  prediction: string;
  null_prediction: string;
  success_criteria: string;
  failure_criteria: string;
  scope: string;
  hypothesis_type: string;
  prior_confidence: number;
  parent_id: string;
  investigation_id: string;
}

export interface ExperimentStartedData {
  experiment_id: string;
  hypothesis_id: string;
  description: string;
  investigation_id: string;
}

export interface ExperimentCompletedData {
  experiment_id: string;
  hypothesis_id: string;
  tool_count: number;
  finding_count: number;
  investigation_id: string;
}

export interface HypothesisEvaluatedData {
  hypothesis_id: string;
  status: HypothesisStatus;
  confidence: number;
  reasoning: string;
  investigation_id: string;
}

export interface NegativeControlData {
  smiles: string;
  name: string;
  prediction_score: number;
  correctly_classified: boolean;
  investigation_id: string;
}

export interface ToolCalledData {
  tool_name: string;
  tool_input: Record<string, unknown>;
  experiment_id?: string;
  investigation_id: string;
}

export interface ToolResultData {
  tool_name: string;
  result_preview: string;
  experiment_id?: string;
  investigation_id: string;
}

export interface FindingRecordedData {
  title: string;
  detail: string;
  hypothesis_id: string;
  evidence_type: EvidenceType;
  evidence?: string;
  source_type?: string;
  source_id?: string;
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
  prompt?: string;
  cost: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    tool_calls: number;
    total_cost_usd: number;
  };
  candidates: CandidateRow[];
  findings?: Finding[];
  hypotheses?: Hypothesis[];
  negative_controls?: NegativeControl[];
}

export interface ErrorData {
  error: string;
  investigation_id: string;
}

export interface OutputSummarizedData {
  tool_name: string;
  original_length: number;
  summarized_length: number;
  investigation_id: string;
}

export interface PhaseChangedData {
  phase: number;
  name: string;
  description: string;
  investigation_id: string;
}

export interface PhaseInfo {
  phase: number;
  name: string;
  description: string;
}

export interface HypothesisApprovalData {
  hypotheses: { id: string; statement: string; rationale: string }[];
  investigation_id: string;
}

export interface CostUpdateData {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  tool_calls: number;
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
  hypothesis_id: string;
  evidence_type: EvidenceType;
  evidence?: string;
  source_type?: string;
  source_id?: string;
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

export interface InvestigationDetail {
  id: string;
  prompt: string;
  status: string;
  hypotheses: Hypothesis[];
  experiments: Experiment[];
  findings: Finding[];
  candidates: CandidateRow[];
  negative_controls: NegativeControl[];
  citations: string[];
  summary: string;
  created_at: string;
  cost_data: Record<string, unknown>;
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

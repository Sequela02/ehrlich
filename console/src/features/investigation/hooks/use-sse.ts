import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import type {
  CandidateRow,
  CompletedData,
  CostInfo,
  EvidenceType,
  Experiment,
  Finding,
  Hypothesis,
  HypothesisStatus,
  NegativeControl,
  SSEEvent,
  SSEEventType,
} from "../types";

const EVENT_TYPES: SSEEventType[] = [
  "hypothesis_formulated",
  "experiment_started",
  "experiment_completed",
  "hypothesis_evaluated",
  "negative_control",
  "tool_called",
  "tool_result",
  "finding_recorded",
  "thinking",
  "error",
  "completed",
  "output_summarized",
];

const MAX_RETRIES = 3;

interface SSEState {
  events: SSEEvent[];
  eventsByExperiment: Map<string, SSEEvent[]>;
  connected: boolean;
  reconnecting: boolean;
  completed: boolean;
  hypotheses: Hypothesis[];
  currentHypothesisId: string;
  currentExperimentId: string;
  experiments: Experiment[];
  negativeControls: NegativeControl[];
  findings: Finding[];
  candidates: CandidateRow[];
  summary: string;
  prompt: string;
  cost: CostInfo | null;
  error: string | null;
  toolCallCount: number;
  activeToolName: string;
  experimentToolCount: number;
  experimentFindingCount: number;
}

export function useSSE(url: string | null): SSEState {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [eventsByExperiment, setEventsByExperiment] = useState<Map<string, SSEEvent[]>>(new Map());
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [currentHypothesisId, setCurrentHypothesisId] = useState("");
  const [currentExperimentId, setCurrentExperimentId] = useState("");
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [negativeControls, setNegativeControls] = useState<NegativeControl[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [summary, setSummary] = useState("");
  const [prompt, setPrompt] = useState("");
  const [cost, setCost] = useState<CostInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toolCallCount, setToolCallCount] = useState(0);
  const [activeToolName, setActiveToolName] = useState("");
  const [experimentToolCount, setExperimentToolCount] = useState(0);
  const [experimentFindingCount, setExperimentFindingCount] = useState(0);
  const sourceRef = useRef<EventSource | null>(null);
  const attemptRef = useRef(0);
  const doneRef = useRef(false);

  const handleEvent = useCallback((eventType: SSEEventType, raw: string) => {
    if (!raw || raw === "undefined") return;

    let parsed: SSEEvent;
    try {
      parsed = JSON.parse(raw) as SSEEvent;
    } catch {
      return;
    }

    const sseEvent: SSEEvent = { event: eventType, data: parsed.data };
    setEvents((prev) => [...prev, sseEvent]);

    switch (eventType) {
      case "hypothesis_formulated": {
        const h: Hypothesis = {
          id: parsed.data.hypothesis_id as string,
          statement: parsed.data.statement as string,
          rationale: parsed.data.rationale as string,
          status: "proposed",
          parent_id: (parsed.data.parent_id as string) || "",
          confidence: 0,
          supporting_evidence: [],
          contradicting_evidence: [],
        };
        setHypotheses((prev) => [...prev, h]);
        setCurrentHypothesisId(h.id);
        break;
      }
      case "experiment_started": {
        const exp: Experiment = {
          id: parsed.data.experiment_id as string,
          hypothesis_id: parsed.data.hypothesis_id as string,
          description: parsed.data.description as string,
          status: "running",
        };
        setExperiments((prev) => [...prev, exp]);
        setCurrentExperimentId(exp.id);
        setCurrentHypothesisId(exp.hypothesis_id);
        setExperimentToolCount(0);
        setExperimentFindingCount(0);
        setActiveToolName("");
        // Mark hypothesis as testing
        setHypotheses((prev) =>
          prev.map((h) =>
            h.id === exp.hypothesis_id ? { ...h, status: "testing" as HypothesisStatus } : h,
          ),
        );
        break;
      }
      case "experiment_completed": {
        const expId = parsed.data.experiment_id as string;
        setExperiments((prev) =>
          prev.map((e) =>
            e.id === expId
              ? {
                  ...e,
                  status: "completed",
                  tool_count: parsed.data.tool_count as number,
                  finding_count: parsed.data.finding_count as number,
                }
              : e,
          ),
        );
        setCurrentExperimentId("");
        setActiveToolName("");
        break;
      }
      case "hypothesis_evaluated": {
        const hId = parsed.data.hypothesis_id as string;
        const status = parsed.data.status as HypothesisStatus;
        const confidence = parsed.data.confidence as number;
        setHypotheses((prev) =>
          prev.map((h) =>
            h.id === hId ? { ...h, status, confidence } : h,
          ),
        );
        break;
      }
      case "negative_control": {
        const nc: NegativeControl = {
          smiles: parsed.data.smiles as string,
          name: parsed.data.name as string,
          prediction_score: parsed.data.prediction_score as number,
          correctly_classified: parsed.data.correctly_classified as boolean,
          source: "",
        };
        setNegativeControls((prev) => [...prev, nc]);
        break;
      }
      case "tool_called": {
        setToolCallCount((prev) => prev + 1);
        setExperimentToolCount((prev) => prev + 1);
        setActiveToolName(parsed.data.tool_name as string);
        const tcExpId = parsed.data.experiment_id as string;
        if (tcExpId) {
          setEventsByExperiment((prev) => {
            const next = new Map(prev);
            const arr = next.get(tcExpId) ?? [];
            next.set(tcExpId, [...arr, sseEvent]);
            return next;
          });
        }
        break;
      }
      case "tool_result": {
        setActiveToolName("");
        const trExpId = parsed.data.experiment_id as string;
        if (trExpId) {
          setEventsByExperiment((prev) => {
            const next = new Map(prev);
            const arr = next.get(trExpId) ?? [];
            next.set(trExpId, [...arr, sseEvent]);
            return next;
          });
        }
        break;
      }
      case "finding_recorded":
        setExperimentFindingCount((prev) => prev + 1);
        setFindings((prev) => [
          ...prev,
          {
            title: parsed.data.title as string,
            detail: parsed.data.detail as string,
            hypothesis_id: (parsed.data.hypothesis_id as string) || "",
            evidence_type: (parsed.data.evidence_type as EvidenceType) || "neutral",
            evidence: (parsed.data.evidence as string) || undefined,
          },
        ]);
        break;
      case "completed": {
        const d = parsed.data as unknown as CompletedData;
        setSummary(d.summary);
        if (d.prompt) setPrompt(d.prompt);
        if (d.candidates) {
          setCandidates(d.candidates);
        }
        if (d.findings && d.findings.length > 0) {
          setFindings((prev) => (prev.length === 0 ? d.findings! : prev));
        }
        if (d.hypotheses && d.hypotheses.length > 0) {
          setHypotheses((prev) => (prev.length === 0 ? d.hypotheses! : prev));
        }
        if (d.negative_controls && d.negative_controls.length > 0) {
          setNegativeControls((prev) => (prev.length === 0 ? d.negative_controls! : prev));
        }
        if (d.cost) {
          const costData = d.cost as Record<string, unknown>;
          setCost({
            inputTokens: costData.input_tokens as number,
            outputTokens: costData.output_tokens as number,
            totalTokens: costData.total_tokens as number,
            totalCost: costData.total_cost_usd as number,
            toolCalls: costData.tool_calls as number,
            byModel: costData.by_model as CostInfo["byModel"],
          });
        }
        setCompleted(true);
        doneRef.current = true;
        toast.success("Investigation complete", {
          description: `${d.candidate_count} candidates identified`,
        });
        if (sourceRef.current) {
          sourceRef.current.close();
          sourceRef.current = null;
        }
        break;
      }
      case "error":
        setError(parsed.data.error as string);
        doneRef.current = true;
        toast.error("Investigation failed", {
          description: parsed.data.error as string,
        });
        if (sourceRef.current) {
          sourceRef.current.close();
          sourceRef.current = null;
        }
        break;
    }
  }, []);

  useEffect(() => {
    if (!url) return;

    function connect() {
      const source = new EventSource(url!);
      sourceRef.current = source;

      source.onopen = () => {
        setConnected(true);
        setReconnecting(false);
        attemptRef.current = 0;
      };

      for (const eventType of EVENT_TYPES) {
        source.addEventListener(eventType, (e: MessageEvent) => {
          handleEvent(eventType, e.data as string);
        });
      }

      source.onerror = () => {
        source.close();
        setConnected(false);

        if (doneRef.current) return;

        if (attemptRef.current < MAX_RETRIES) {
          setReconnecting(true);
          const delay = Math.pow(2, attemptRef.current) * 1000;
          attemptRef.current += 1;
          setTimeout(connect, delay);
        } else {
          setReconnecting(false);
        }
      };
    }

    connect();

    return () => {
      if (sourceRef.current) {
        sourceRef.current.close();
        sourceRef.current = null;
      }
      attemptRef.current = MAX_RETRIES;
    };
  }, [url, handleEvent]);

  return {
    events,
    eventsByExperiment,
    connected,
    reconnecting,
    completed,
    hypotheses,
    currentHypothesisId,
    currentExperimentId,
    experiments,
    negativeControls,
    findings,
    candidates,
    summary,
    prompt,
    cost,
    error,
    toolCallCount,
    activeToolName,
    experimentToolCount,
    experimentFindingCount,
  };
}

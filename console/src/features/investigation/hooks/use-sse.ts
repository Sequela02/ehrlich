import { useCallback, useEffect, useRef, useState } from "react";
import type {
  CandidateRow,
  CompletedData,
  CostInfo,
  Finding,
  SSEEvent,
  SSEEventType,
} from "../types";

const EVENT_TYPES: SSEEventType[] = [
  "phase_started",
  "tool_called",
  "tool_result",
  "finding_recorded",
  "thinking",
  "error",
  "completed",
  "director_planning",
  "director_decision",
  "output_summarized",
];

const MAX_RETRIES = 3;

interface SSEState {
  events: SSEEvent[];
  connected: boolean;
  reconnecting: boolean;
  completed: boolean;
  currentPhase: string;
  completedPhases: string[];
  findings: Finding[];
  candidates: CandidateRow[];
  summary: string;
  cost: CostInfo | null;
  error: string | null;
  toolCallCount: number;
}

export function useSSE(url: string | null): SSEState {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("");
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [summary, setSummary] = useState("");
  const [cost, setCost] = useState<CostInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toolCallCount, setToolCallCount] = useState(0);
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
      case "phase_started":
        setCurrentPhase((prevPhase) => {
          if (prevPhase && prevPhase !== (parsed.data.phase as string)) {
            setCompletedPhases((prev) =>
              prev.includes(prevPhase) ? prev : [...prev, prevPhase],
            );
          }
          return parsed.data.phase as string;
        });
        break;
      case "tool_called":
        setToolCallCount((prev) => prev + 1);
        break;
      case "finding_recorded":
        setFindings((prev) => [
          ...prev,
          {
            title: parsed.data.title as string,
            detail: parsed.data.detail as string,
            phase: parsed.data.phase as string,
            evidence: (parsed.data.evidence as string) || undefined,
          },
        ]);
        break;
      case "completed": {
        const d = parsed.data as unknown as CompletedData;
        setSummary(d.summary);
        if (d.candidates) {
          setCandidates(d.candidates);
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
        if (sourceRef.current) {
          sourceRef.current.close();
          sourceRef.current = null;
        }
        break;
      }
      case "error":
        setError(parsed.data.error as string);
        doneRef.current = true;
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
      attemptRef.current = MAX_RETRIES; // Prevent reconnect after unmount
    };
  }, [url, handleEvent]);

  return {
    events,
    connected,
    reconnecting,
    completed,
    currentPhase,
    completedPhases,
    findings,
    candidates,
    summary,
    cost,
    error,
    toolCallCount,
  };
}

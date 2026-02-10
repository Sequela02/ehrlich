import { useCallback, useEffect, useRef, useState } from "react";
import type {
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
];

interface SSEState {
  events: SSEEvent[];
  connected: boolean;
  completed: boolean;
  currentPhase: string;
  findings: Finding[];
  summary: string;
  cost: CostInfo | null;
  error: string | null;
}

export function useSSE(url: string | null): SSEState {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [summary, setSummary] = useState("");
  const [cost, setCost] = useState<CostInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  const handleEvent = useCallback((eventType: SSEEventType, raw: string) => {
    const parsed = JSON.parse(raw) as SSEEvent;
    const sseEvent: SSEEvent = { event: eventType, data: parsed.data };
    setEvents((prev) => [...prev, sseEvent]);

    switch (eventType) {
      case "phase_started":
        setCurrentPhase(parsed.data.phase as string);
        break;
      case "finding_recorded":
        setFindings((prev) => [
          ...prev,
          {
            title: parsed.data.title as string,
            detail: parsed.data.detail as string,
            phase: parsed.data.phase as string,
          },
        ]);
        break;
      case "completed": {
        const d = parsed.data as unknown as CompletedData;
        setSummary(d.summary);
        if (d.cost) {
          setCost({
            inputTokens: d.cost.input_tokens,
            outputTokens: d.cost.output_tokens,
            totalTokens: d.cost.total_tokens,
            totalCost: d.cost.total_cost_usd,
            toolCalls: d.cost.tool_calls,
          });
        }
        setCompleted(true);
        break;
      }
      case "error":
        setError(parsed.data.error as string);
        break;
    }
  }, []);

  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => setConnected(true);

    for (const eventType of EVENT_TYPES) {
      source.addEventListener(eventType, (e: MessageEvent) => {
        handleEvent(eventType, e.data as string);
      });
    }

    source.onerror = () => {
      setConnected(false);
      source.close();
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [url, handleEvent]);

  return { events, connected, completed, currentPhase, findings, summary, cost, error };
}

import { useEffect, useRef, useState } from "react";
import type { SSEEvent } from "../types";

export function useSSE(url: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => setConnected(true);

    source.onmessage = (e) => {
      const parsed = JSON.parse(e.data) as SSEEvent;
      setEvents((prev) => [...prev, parsed]);
    };

    source.onerror = () => {
      setConnected(false);
      source.close();
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [url]);

  return { events, connected };
}

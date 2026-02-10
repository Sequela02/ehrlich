import type { SSEEvent } from "../types";

interface TimelineProps {
  events: SSEEvent[];
}

export function Timeline({ events }: TimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Waiting for events...
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event, i) => (
        <div key={i} className="rounded-lg border border-border p-3">
          <span className="text-xs font-medium text-primary">
            {event.event}
          </span>
          <pre className="mt-1 text-xs text-muted-foreground">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
}

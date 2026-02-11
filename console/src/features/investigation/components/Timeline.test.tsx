import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Timeline } from "./Timeline";
import type { SSEEvent } from "../types";

describe("Timeline", () => {
  it("shows connecting message when no events", () => {
    render(<Timeline events={[]} />);
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
  });

  it("renders hypothesis_formulated event", () => {
    const events: SSEEvent[] = [
      { event: "hypothesis_formulated", data: { statement: "Compound X inhibits target Y", rationale: "Based on literature", hypothesis_id: "h1", parent_id: "" } },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText(/Compound X inhibits target Y/)).toBeInTheDocument();
  });

  it("renders tool_called event", () => {
    const events: SSEEvent[] = [
      {
        event: "tool_called",
        data: { tool_name: "search_literature", tool_input: { query: "MRSA" } },
      },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText("search_literature")).toBeInTheDocument();
  });

  it("renders finding_recorded event", () => {
    const events: SSEEvent[] = [
      {
        event: "finding_recorded",
        data: { title: "Key insight", detail: "Detail text", hypothesis_id: "h1", evidence_type: "supporting" },
      },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText(/Key insight/)).toBeInTheDocument();
  });

  it("renders thinking event", () => {
    const events: SSEEvent[] = [
      { event: "thinking", data: { text: "Let me analyze the data..." } },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText(/Let me analyze/)).toBeInTheDocument();
  });

  it("renders error event", () => {
    const events: SSEEvent[] = [
      { event: "error", data: { error: "API timeout" } },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText("API timeout")).toBeInTheDocument();
  });

  it("renders completed event", () => {
    const events: SSEEvent[] = [
      { event: "completed", data: { candidate_count: 3 } },
    ];
    render(<Timeline events={events} />);
    expect(screen.getByText(/3 candidates/)).toBeInTheDocument();
  });
});

import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { LiveLabViewer } from "./LiveLabViewer";

const mockViewer = {
  render: vi.fn(),
  clear: vi.fn(),
  addModel: vi.fn(),
  setStyle: vi.fn(),
  zoomTo: vi.fn(),
  addLabel: vi.fn(),
};

vi.mock("3dmol", () => ({
  createViewer: vi.fn(() => mockViewer),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("LiveLabViewer", () => {
  it("renders container", () => {
    const { container } = render(
      <LiveLabViewer events={[]} completed={false} />,
    );
    expect(container.querySelector(".bg-\\[\\#0f1219\\]")).toBeInTheDocument();
  });

  it("shows waiting message when no content and not completed", () => {
    render(<LiveLabViewer events={[]} completed={false} />);
    const messages = screen.getAllByText(/waiting for molecular data/i);
    expect(messages.length).toBeGreaterThanOrEqual(1);
  });

  it("shows no-data message when completed with no content", () => {
    render(<LiveLabViewer events={[]} completed={true} />);
    const messages = screen.getAllByText(/no molecular data was visualized/i);
    expect(messages.length).toBeGreaterThanOrEqual(1);
  });
});

import { render, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock hooks before importing component
vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
}));

vi.mock("../hooks/use-investigation", () => ({
  useInvestigation: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
}));

vi.mock("../hooks/use-credits", () => ({
  useCredits: () => ({
    data: { credits: 10, is_byok: false },
  }),
}));

vi.mock("../hooks/use-upload", () => ({
  useUpload: () => ({
    mutateAsync: vi.fn(),
    isError: false,
  }),
}));

import { PromptInput } from "./PromptInput";

function renderWithProvider(props: { value: string; onChange: (v: string) => void }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PromptInput {...props} />
    </QueryClientProvider>,
  );
}

describe("PromptInput", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders default tier label", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    const text = container.textContent ?? "";
    // Default tier is Opus, shown on the popover trigger button
    expect(text).toContain("Opus");
  });

  it("renders textarea", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    const textareas = container.querySelectorAll("textarea");
    expect(textareas.length).toBe(1);
  });

  it("calls onChange when typing", () => {
    const onChange = vi.fn();
    const { container } = renderWithProvider({ value: "", onChange });
    const textarea = container.querySelector("textarea")!;
    fireEvent.change(textarea, { target: { value: "Test query" } });
    expect(onChange).toHaveBeenCalledWith("Test query");
  });

  it("renders submit button", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    // Submit button is type="button" with an ArrowUp icon
    const buttons = container.querySelectorAll('button[type="button"]');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("renders attach files button", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    const attachBtn = container.querySelector('button[title="Attach files"]');
    expect(attachBtn).not.toBeNull();
  });
});

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

  it("renders tier selector buttons", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    const text = container.textContent ?? "";
    expect(text).toContain("Haiku");
    expect(text).toContain("Sonnet");
    expect(text).toContain("Opus");
  });

  it("renders credit costs", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    const text = container.textContent ?? "";
    expect(text).toContain("1cr");
    expect(text).toContain("3cr");
    expect(text).toContain("5cr");
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
    const submitBtn = container.querySelector('button[type="submit"]');
    expect(submitBtn).not.toBeNull();
    expect(submitBtn!.textContent).toContain("Start Investigation");
  });

  it("renders director label", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    expect(container.textContent).toContain("Director");
  });

  it("renders FileUpload drop zone", () => {
    const { container } = renderWithProvider({ value: "", onChange: vi.fn() });
    expect(container.textContent).toContain("Drop CSV, Excel, or PDF");
  });
});

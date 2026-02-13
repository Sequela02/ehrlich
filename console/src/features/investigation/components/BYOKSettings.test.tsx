import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BYOKSettings } from "./BYOKSettings";

function renderWithProvider() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BYOKSettings />
    </QueryClientProvider>,
  );
}

describe("BYOKSettings", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders input when no key stored", () => {
    renderWithProvider();
    expect(screen.getByPlaceholderText("sk-ant-...")).toBeInTheDocument();
  });

  it("saves key to localStorage", () => {
    renderWithProvider();
    const input = screen.getByPlaceholderText("sk-ant-...");
    fireEvent.change(input, { target: { value: "sk-ant-test123" } });
    const saveButtons = screen.getAllByRole("button");
    const saveButton = saveButtons.find((b) => b.textContent === "Save");
    expect(saveButton).toBeDefined();
    fireEvent.click(saveButton!);
    expect(localStorage.getItem("ehrlich_api_key")).toBe("sk-ant-test123");
  });

  it("shows stored key indicator", () => {
    localStorage.setItem("ehrlich_api_key", "sk-ant-mykey123");
    renderWithProvider();
    expect(screen.getByText(/Using your own key/)).toBeInTheDocument();
  });

  it("clears key on remove click", () => {
    localStorage.setItem("ehrlich_api_key", "sk-ant-remove");
    renderWithProvider();
    const removeButtons = screen.getAllByRole("button");
    const removeButton = removeButtons.find((b) => b.textContent?.includes("Remove"));
    expect(removeButton).toBeDefined();
    fireEvent.click(removeButton!);
    expect(localStorage.getItem("ehrlich_api_key")).toBeNull();
  });

  it("renders BYOK heading", () => {
    renderWithProvider();
    expect(screen.getAllByText("Bring Your Own Key").length).toBeGreaterThanOrEqual(1);
  });

  it("shows helper text when no key", () => {
    renderWithProvider();
    expect(
      screen.getByText(/provide your anthropic api key/i),
    ).toBeInTheDocument();
  });
});

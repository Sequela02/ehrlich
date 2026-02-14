import { render, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { UploadResponse } from "../types";

const mockMutateAsync = vi.fn();
const mockUploadState = { mutateAsync: mockMutateAsync, isError: false };

vi.mock("../hooks/use-upload", () => ({
  useUpload: () => mockUploadState,
}));

import { FileUpload } from "./FileUpload";

function renderWithProvider(
  props: { onFilesChanged: (files: { file_id: string; filename: string }[]) => void },
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FileUpload {...props} />
    </QueryClientProvider>,
  );
}

describe("FileUpload", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    mockUploadState.isError = false;
  });

  it("renders drop zone with instruction text", () => {
    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    const text = container.textContent ?? "";
    expect(text).toContain("Drop CSV, Excel, or PDF files here");
  });

  it("renders hidden file input with accepted types", () => {
    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).not.toBeNull();
    expect(input.accept).toBe(".csv,.xlsx,.pdf");
    expect(input.multiple).toBe(true);
  });

  it("shows uploaded files via DataPreview after upload", async () => {
    const uploadResult: UploadResponse = {
      file_id: "abc-123",
      filename: "test.csv",
      content_type: "text/csv",
      preview: {
        columns: ["col1", "col2"],
        dtypes: ["str", "int"],
        row_count: 10,
        sample_rows: [["a", "1"]],
      },
    };
    mockMutateAsync.mockResolvedValueOnce(uploadResult);

    const onFilesChanged = vi.fn();
    const { container } = renderWithProvider({ onFilesChanged });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["data"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    // Wait for async upload
    await vi.waitFor(() => {
      expect(container.textContent).toContain("test.csv");
    });

    expect(onFilesChanged).toHaveBeenCalledWith([
      { file_id: "abc-123", filename: "test.csv" },
    ]);
  });

  it("removes file when remove button is clicked", async () => {
    const uploadResult: UploadResponse = {
      file_id: "abc-123",
      filename: "test.csv",
      content_type: "text/csv",
      preview: {
        columns: ["col1"],
        dtypes: ["str"],
        row_count: 5,
        sample_rows: [["x"]],
      },
    };
    mockMutateAsync.mockResolvedValueOnce(uploadResult);

    const onFilesChanged = vi.fn();
    const { container } = renderWithProvider({ onFilesChanged });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["data"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    await vi.waitFor(() => {
      expect(container.textContent).toContain("test.csv");
    });

    // Click remove button (the X button inside DataPreview)
    const removeBtn = container.querySelector(
      ".relative button",
    ) as HTMLButtonElement;
    fireEvent.click(removeBtn);

    expect(container.textContent).not.toContain("test.csv");
    expect(onFilesChanged).toHaveBeenLastCalledWith([]);
  });

  it("shows error message when upload fails", () => {
    mockUploadState.isError = true;
    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    expect(container.textContent).toContain("Upload failed");
  });
});

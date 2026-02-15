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
    expect(text).toContain("Drop CSV, Excel, or PDF");
  });

  it("renders hidden file input with accepted types", () => {
    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).not.toBeNull();
    expect(input.accept).toBe(".csv,.xlsx,.pdf");
    expect(input.multiple).toBe(true);
  });

  it("uploads file and calls onFilesChanged", async () => {
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

    // Wait for async upload to complete
    await vi.waitFor(() => {
      expect(onFilesChanged).toHaveBeenCalledWith([
        expect.objectContaining({ file_id: "abc-123", filename: "test.csv" }),
      ]);
    });
  });

  it("shows per-file error when upload fails", async () => {
    mockMutateAsync.mockRejectedValueOnce({ message: "Unsupported file type" });

    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["data"], "bad.json", { type: "application/json" });
    fireEvent.change(input, { target: { files: [file] } });

    await vi.waitFor(() => {
      expect(container.textContent).toContain("bad.json");
      expect(container.textContent).toContain("Unsupported file type");
    });
  });

  it("rejects oversized file without calling upload", () => {
    const onFilesChanged = vi.fn();
    const { container } = renderWithProvider({ onFilesChanged });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    // Create a file that reports > 50 MB
    const bigFile = new File(["x"], "huge.csv", { type: "text/csv" });
    Object.defineProperty(bigFile, "size", { value: 51 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [bigFile] } });

    expect(container.textContent).toContain("huge.csv");
    expect(container.textContent).toContain("File too large");
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it("shows file count after upload", async () => {
    const uploadResult: UploadResponse = {
      file_id: "f-1",
      filename: "a.csv",
      content_type: "text/csv",
      preview: { columns: ["x"], dtypes: ["int"], row_count: 1, sample_rows: [["1"]] },
    };
    mockMutateAsync.mockResolvedValueOnce(uploadResult);

    const { container } = renderWithProvider({ onFilesChanged: vi.fn() });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["d"], "a.csv")] } });

    await vi.waitFor(() => {
      expect(container.textContent).toContain("1 / 10 files");
    });
  });
});

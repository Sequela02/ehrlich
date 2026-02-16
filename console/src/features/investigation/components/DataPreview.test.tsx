import { render, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { DataPreview } from "./DataPreview";
import type { TabularPreview, DocumentPreview } from "../types";

const tabularPreview: TabularPreview = {
  columns: ["name", "age", "score"],
  dtypes: ["str", "int", "float"],
  row_count: 150,
  sample_rows: [
    ["Alice", "30", "95.5"],
    ["Bob", "25", "88.0"],
  ],
};

const documentPreview: DocumentPreview = {
  text: "This is a sample PDF document with some content for testing purposes.",
  page_count: 3,
};

describe("DataPreview", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders filename", () => {
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={vi.fn()}
      />,
    );
    expect(container.textContent).toContain("data.csv");
  });

  it("renders tabular preview with column names", () => {
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).toContain("name");
    expect(text).toContain("age");
    expect(text).toContain("score");
  });

  it("renders tabular preview with sample rows", () => {
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).toContain("Alice");
    expect(text).toContain("Bob");
    expect(text).toContain("95.5");
  });

  it("renders tabular row count badge", () => {
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).toContain("150 rows");
    expect(text).toContain("3 columns");
  });

  it("renders document preview with text excerpt", () => {
    const { container } = render(
      <DataPreview
        filename="report.pdf"
        contentType="application/pdf"
        preview={documentPreview}
        onRemove={vi.fn()}
      />,
    );
    expect(container.textContent).toContain("sample PDF document");
  });

  it("renders document page count badge", () => {
    const { container } = render(
      <DataPreview
        filename="report.pdf"
        contentType="application/pdf"
        preview={documentPreview}
        onRemove={vi.fn()}
      />,
    );
    expect(container.textContent).toContain("3 pages");
  });

  it("renders singular page label for single page", () => {
    const singlePage: DocumentPreview = { text: "Content", page_count: 1 };
    const { container } = render(
      <DataPreview
        filename="one.pdf"
        contentType="application/pdf"
        preview={singlePage}
        onRemove={vi.fn()}
      />,
    );
    expect(container.textContent).toContain("1 page");
    expect(container.textContent).not.toContain("1 pages");
  });

  it("calls onRemove when remove button is clicked", () => {
    const onRemove = vi.fn();
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={onRemove}
      />,
    );
    const removeBtn = container.querySelector("button")!;
    fireEvent.click(removeBtn);
    expect(onRemove).toHaveBeenCalledOnce();
  });

  it("truncates long document text at 300 chars", () => {
    const longText: DocumentPreview = {
      text: "A".repeat(400),
      page_count: 5,
    };
    const { container } = render(
      <DataPreview
        filename="long.pdf"
        contentType="application/pdf"
        preview={longText}
        onRemove={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).toContain("...");
    expect(text).not.toContain("A".repeat(400));
  });

  it("renders dtypes next to column names", () => {
    const { container } = render(
      <DataPreview
        filename="data.csv"
        contentType="text/csv"
        preview={tabularPreview}
        onRemove={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).toContain("str");
    expect(text).toContain("int");
    expect(text).toContain("float");
  });
});

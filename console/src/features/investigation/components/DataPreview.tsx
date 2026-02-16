import { X } from "lucide-react";
import type { TabularPreview, DocumentPreview } from "../types";

interface DataPreviewProps {
  filename: string;
  contentType: string;
  preview: TabularPreview | DocumentPreview;
  onRemove: () => void;
}

function isTabular(preview: TabularPreview | DocumentPreview): preview is TabularPreview {
  return "columns" in preview;
}

export function DataPreview({ filename, preview, onRemove }: DataPreviewProps) {
  return (
    <div className="relative rounded-md border border-border bg-surface p-3">
      <button
        type="button"
        onClick={onRemove}
        className="absolute right-2 top-2 rounded-sm p-0.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <X className="h-3.5 w-3.5" />
      </button>

      <p className="truncate pr-6 font-mono text-xs font-medium text-foreground">
        {filename}
      </p>

      {isTabular(preview) ? (
        <div className="mt-2 space-y-2">
          <div className="flex flex-wrap gap-1">
            {preview.columns.map((col, i) => (
              <span
                key={col}
                className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                {col}
                <span className="ml-0.5 opacity-50">{preview.dtypes[i]}</span>
              </span>
            ))}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse font-mono text-[11px]">
              <thead>
                <tr>
                  {preview.columns.map((col) => (
                    <th
                      key={col}
                      className="border-b border-border/50 px-2 py-1 text-left text-[10px] font-medium text-muted-foreground"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.sample_rows.slice(0, 5).map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        className="truncate border-b border-border/30 px-2 py-0.5 text-foreground/80"
                        style={{ maxWidth: 160 }}
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2">
            <span className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {preview.row_count.toLocaleString()} rows
            </span>
            <span className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {preview.columns.length} columns
            </span>
          </div>
        </div>
      ) : (
        <div className="mt-2 space-y-2">
          <p className="line-clamp-4 font-mono text-[11px] leading-relaxed text-foreground/70">
            {preview.text.length > 300
              ? preview.text.slice(0, 300) + "..."
              : preview.text}
          </p>
          <span className="inline-block rounded-sm bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
            {preview.page_count} {preview.page_count === 1 ? "page" : "pages"}
          </span>
        </div>
      )}
    </div>
  );
}

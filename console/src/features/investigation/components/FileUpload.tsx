import { useCallback, useRef, useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import { useUpload } from "../hooks/use-upload";
import { DataPreview } from "./DataPreview";
import type { UploadResponse } from "../types";

const ACCEPTED_TYPES = ".csv,.xlsx,.pdf";
const MAX_FILES = 10;

interface UploadedFile extends UploadResponse {
  // UploadResponse already has file_id, filename, content_type, preview
}

interface FileUploadProps {
  onFilesChanged: (files: { file_id: string; filename: string }[]) => void;
}

export function FileUpload({ onFilesChanged }: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUpload();

  const updateParent = useCallback(
    (updated: UploadedFile[]) => {
      onFilesChanged(
        updated.map((f) => ({ file_id: f.file_id, filename: f.filename })),
      );
    },
    [onFilesChanged],
  );

  function handleRemove(fileId: string) {
    setFiles((prev) => {
      const updated = prev.filter((f) => f.file_id !== fileId);
      updateParent(updated);
      return updated;
    });
  }

  async function processFile(file: File) {
    setPendingCount((c) => c + 1);
    try {
      const result = await upload.mutateAsync(file);
      setFiles((prev) => {
        const updated = [...prev, result];
        updateParent(updated);
        return updated;
      });
    } finally {
      setPendingCount((c) => c - 1);
    }
  }

  function handleFiles(fileList: FileList | File[]) {
    const incoming = Array.from(fileList);
    const remaining = MAX_FILES - files.length;
    const batch = incoming.slice(0, remaining);
    for (const file of batch) {
      void processFile(file);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
      e.target.value = "";
    }
  }

  const atCapacity = files.length >= MAX_FILES;

  return (
    <div className="space-y-2">
      {!atCapacity && (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`flex w-full items-center justify-center gap-2 rounded-md border border-dashed px-4 py-3 text-xs transition-colors ${
            dragOver
              ? "border-primary bg-primary/5 text-primary"
              : "border-border text-muted-foreground hover:border-muted-foreground/50 hover:text-foreground"
          }`}
        >
          {pendingCount > 0 ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Upload className="h-4 w-4" />
          )}
          <span className="font-mono text-[11px]">
            {pendingCount > 0
              ? `Uploading ${pendingCount} file${pendingCount > 1 ? "s" : ""}...`
              : "Drop CSV, Excel, or PDF files here, or click to browse"}
          </span>
        </button>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        multiple
        onChange={handleInputChange}
        className="hidden"
      />

      {upload.isError && (
        <p className="font-mono text-[11px] text-destructive">
          Upload failed. Check file type and try again.
        </p>
      )}

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f) => (
            <DataPreview
              key={f.file_id}
              filename={f.filename}
              contentType={f.content_type}
              preview={f.preview}
              onRemove={() => handleRemove(f.file_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

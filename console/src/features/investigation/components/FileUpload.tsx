import { useCallback, useRef, useState } from "react";
import { Upload, Loader2, AlertCircle } from "lucide-react";
import { useUpload } from "../hooks/use-upload";
import { DataPreview } from "./DataPreview";
import type { UploadResponse } from "../types";

const ACCEPTED_TYPES = ".csv,.xlsx,.pdf";
const MAX_FILES = 10;
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

interface UploadedFile extends UploadResponse {
  // UploadResponse already has file_id, filename, content_type, preview
}

interface FileUploadProps {
  onFilesChanged: (files: { file_id: string; filename: string }[]) => void;
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${bytes} B`;
}

export function FileUpload({ onFilesChanged }: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [errors, setErrors] = useState<{ name: string; message: string }[]>([]);
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

  function addError(name: string, message: string) {
    setErrors((prev) => [...prev, { name, message }]);
  }

  function dismissError(index: number) {
    setErrors((prev) => prev.filter((_, i) => i !== index));
  }

  function handleRemove(fileId: string) {
    setFiles((prev) => {
      const updated = prev.filter((f) => f.file_id !== fileId);
      updateParent(updated);
      return updated;
    });
  }

  async function processFile(file: File) {
    if (file.size > MAX_FILE_SIZE) {
      addError(file.name, `File too large (${formatSize(file.size)}). Maximum is ${formatSize(MAX_FILE_SIZE)}.`);
      return;
    }

    setPendingCount((c) => c + 1);
    try {
      const result = await upload.mutateAsync(file);
      setFiles((prev) => {
        const updated = [...prev, result];
        updateParent(updated);
        return updated;
      });
    } catch (err: unknown) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String((err as { message: string }).message)
          : "Upload failed";
      addError(file.name, detail);
    } finally {
      setPendingCount((c) => c - 1);
    }
  }

  function handleFiles(fileList: FileList | File[]) {
    const incoming = Array.from(fileList);
    const remaining = MAX_FILES - files.length;
    if (incoming.length > remaining) {
      addError(
        `${incoming.length} files`,
        `Only ${remaining} more file${remaining === 1 ? "" : "s"} allowed (max ${MAX_FILES}).`,
      );
    }
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
          className={`flex w-full items-center justify-center gap-2 rounded-md border border-dashed px-4 py-3 text-xs transition-colors ${dragOver
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

      {files.length > 0 && (
        <p className="font-mono text-[10px] text-muted-foreground">
          {files.length} / {MAX_FILES} files
        </p>
      )}

      {errors.length > 0 && (
        <div className="space-y-1">
          {errors.map((err, i) => (
            <div
              key={`${err.name}-${i}`}
              className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2"
            >
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
              <p className="flex-1 font-mono text-[11px] text-destructive">
                <span className="font-semibold">{err.name}:</span> {err.message}
              </p>
              <button
                type="button"
                onClick={() => dismissError(i)}
                className="font-mono text-[11px] text-destructive/60 hover:text-destructive"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
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


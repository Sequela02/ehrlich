import { useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ArrowUp, Paperclip, Brain } from "lucide-react";
import { useInvestigation } from "../hooks/use-investigation";
import { useCredits } from "../hooks/use-credits";
import { FileUpload, type FileUploadRef, type UploadedFile } from "./FileUpload";
import type { DirectorTier } from "../types";
import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/shared/components/ui/popover";
import { cn } from "@/shared/lib/utils";

const TIERS: { value: DirectorTier; label: string; credits: number }[] = [
  { value: "haiku", label: "Haiku", credits: 1 },
  { value: "sonnet", label: "Sonnet", credits: 3 },
  { value: "opus", label: "Opus", credits: 5 },
];

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function PromptInput({ value, onChange }: PromptInputProps) {
  const navigate = useNavigate();
  const mutation = useInvestigation();
  const { data: creditData } = useCredits();
  const [tier, setTier] = useState<DirectorTier>("opus");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const fileUploadRef = useRef<FileUploadRef>(null);

  const selectedTier = TIERS.find((t) => t.value === tier) || TIERS[2];
  const isByok = creditData?.is_byok ?? false;
  const hasEnoughCredits =
    isByok || !creditData || creditData.credits >= selectedTier.credits;

  function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!value.trim() || mutation.isPending || !hasEnoughCredits) return;

    const fileIds = uploadedFiles.map((f) => f.file_id);
    mutation.mutate(
      {
        prompt: value.trim(),
        director_tier: tier,
        ...(fileIds.length > 0 && { file_ids: fileIds }),
      },
      {
        onSuccess: (data) => {
          void navigate({ to: "/investigation/$id", params: { id: data.id } });
        },
      },
    );
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  const [isDragging, setIsDragging] = useState(false);

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      // Cast FileList to File[] for the ref method. 
      // Actually ref.addFiles expects File[]. Array.from() works.
      fileUploadRef.current?.addFiles(Array.from(e.dataTransfer.files));
    }
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative flex flex-col rounded-xl border bg-background shadow-sm transition-all focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/50 ${isDragging ? "border-primary ring-1 ring-primary" : "border-border"
        }`}
    >

      <Textarea
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          e.target.style.height = 'auto';
          e.target.style.height = `${e.target.scrollHeight}px`;
        }}
        onKeyDown={handleKeyDown}
        placeholder="Describe your research question..."
        className="min-h-[60px] w-full resize-none border-0 bg-transparent px-4 py-3 shadow-none focus-visible:ring-0 overflow-y-hidden"
        style={{ minHeight: "80px" }}
      />

      {/* File Upload Component (List rendered here) */}
      <div className="px-3">
        <FileUpload
          ref={fileUploadRef}
          onFilesChanged={setUploadedFiles}
          trigger={<></>} // Hidden trigger, we use custom button
        />
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 pl-3">
        <div className="flex items-center gap-2">
          {/* File Upload Trigger */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={() => fileUploadRef.current?.open()}
            type="button"
            title="Attach files"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          {/* Director Tier Selector */}

          {/* Director Tier Selector - Popover Style */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-2 border-dashed px-2 text-xs font-medium"
                title="Select Director Tier"
              >
                <Brain className="h-3.5 w-3.5" />
                {selectedTier.label}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="start">
              <div className="grid gap-1 p-2">
                <div className="mb-2 px-2 pt-1">
                  <h4 className="font-medium leading-none">Director Tier</h4>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Higher tiers provide more reasoning depth but cost more credits.
                  </p>
                </div>
                {TIERS.map((t) => (
                  <button
                    key={t.value}
                    onClick={() => {
                      setTier(t.value);
                      // Optional: close popover on select? 
                      // Popover primitive doesn't auto-close unless we control open state or use DialogClose inside.
                      // For now we just select. User clicks outside to close.
                    }}
                    className={cn(
                      "flex flex-col items-start gap-1 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                      tier === t.value && "bg-accent text-accent-foreground"
                    )}
                  >
                    <div className="flex w-full items-center justify-between">
                      <span className="font-medium">{t.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {t.credits} cr
                      </span>
                    </div>
                    <span className="text-[10px] text-muted-foreground/80">
                      {t.value === "haiku" && "Fast & efficient for simple queries."}
                      {t.value === "sonnet" && "Balanced reasoning and speed."}
                      {t.value === "opus" && "Maximum reasoning power for complex tasks."}
                    </span>
                  </button>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        </div>

        <div className="flex items-center gap-3">
          {!hasEnoughCredits && (
            <span className="text-[10px] text-destructive">
              Insufficient credits
            </span>
          )}
          <Button
            size="icon"
            type="button"
            onClick={(e) => handleSubmit(e)}
            disabled={!value.trim() || mutation.isPending || !hasEnoughCredits}
            className="h-8 w-8 rounded-lg"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {mutation.isError && (
        <div className="absolute -bottom-6 left-0 text-[10px] text-destructive">
          Failed to start. Please try again.
        </div>
      )}
    </div>
  );
}

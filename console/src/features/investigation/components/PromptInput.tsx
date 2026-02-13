import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useInvestigation } from "../hooks/use-investigation";
import { useCredits } from "../hooks/use-credits";
import type { DirectorTier } from "../types";

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

  const selectedTier = TIERS.find((t) => t.value === tier)!;
  const isByok = creditData?.is_byok ?? false;
  const hasEnoughCredits =
    isByok || !creditData || creditData.credits >= selectedTier.credits;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim() || mutation.isPending || !hasEnoughCredits) return;

    mutation.mutate(
      { prompt: value.trim(), director_tier: tier },
      {
        onSuccess: (data) => {
          void navigate({ to: "/investigation/$id", params: { id: data.id } });
        },
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe your research question...&#10;&#10;Example: Find novel drug candidates for a specific disease target or screen compounds for desired properties"
        className="w-full rounded-lg border border-border bg-surface p-4 text-sm leading-relaxed placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/40"
        rows={5}
      />
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-1">
          <span className="mr-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            Director
          </span>
          {TIERS.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setTier(t.value)}
              className={`rounded px-2.5 py-1 font-mono text-[11px] transition-colors ${
                tier === t.value
                  ? "bg-primary text-primary-foreground"
                  : "border border-border text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {t.label}
              {!isByok && (
                <span className="ml-1 opacity-70">{t.credits}cr</span>
              )}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {mutation.isError && (
            <p className="text-sm text-destructive">
              Failed to start investigation.
            </p>
          )}
          {!hasEnoughCredits && (
            <p className="font-mono text-[11px] text-destructive">
              Insufficient credits
            </p>
          )}
          <button
            type="submit"
            disabled={!value.trim() || mutation.isPending || !hasEnoughCredits}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 hover:shadow-[0_0_12px_oklch(0.72_0.19_155_/_0.3)] disabled:opacity-50 disabled:hover:shadow-none"
          >
            {mutation.isPending ? "Starting..." : "Start Investigation"}
          </button>
        </div>
      </div>
    </form>
  );
}

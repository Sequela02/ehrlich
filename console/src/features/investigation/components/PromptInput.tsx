import { useNavigate } from "@tanstack/react-router";
import { useInvestigation } from "../hooks/use-investigation";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function PromptInput({ value, onChange }: PromptInputProps) {
  const navigate = useNavigate();
  const mutation = useInvestigation();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim() || mutation.isPending) return;

    mutation.mutate(
      { prompt: value.trim() },
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
      {mutation.isError && (
        <p className="text-sm text-destructive">
          Failed to start investigation. Is the server running?
        </p>
      )}
      <button
        type="submit"
        disabled={!value.trim() || mutation.isPending}
        className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 hover:shadow-[0_0_12px_oklch(0.72_0.19_155_/_0.3)] disabled:opacity-50 disabled:hover:shadow-none"
      >
        {mutation.isPending ? "Starting..." : "Start Investigation"}
      </button>
    </form>
  );
}

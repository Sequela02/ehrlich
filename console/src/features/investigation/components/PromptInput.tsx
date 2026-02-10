import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useInvestigation } from "../hooks/use-investigation";

export function PromptInput() {
  const [prompt, setPrompt] = useState("");
  const navigate = useNavigate();
  const mutation = useInvestigation();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || mutation.isPending) return;

    mutation.mutate(
      { prompt: prompt.trim() },
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
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your antimicrobial research question...&#10;&#10;Example: Find novel antimicrobial candidates against MRSA (methicillin-resistant Staphylococcus aureus)"
        className="w-full rounded-lg border border-border bg-background p-4 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/50"
        rows={5}
      />
      {mutation.isError && (
        <p className="text-sm text-destructive">
          Failed to start investigation. Is the server running?
        </p>
      )}
      <button
        type="submit"
        disabled={!prompt.trim() || mutation.isPending}
        className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        {mutation.isPending ? "Starting..." : "Start Investigation"}
      </button>
    </form>
  );
}

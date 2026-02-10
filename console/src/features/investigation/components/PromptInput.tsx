import { useState } from "react";

export function PromptInput() {
  const [prompt, setPrompt] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    // TODO: Wire to use-investigation hook
    console.log("Submitting:", prompt);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe your antimicrobial research question..."
        className="w-full rounded-lg border border-border bg-background p-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        rows={4}
      />
      <button
        type="submit"
        disabled={!prompt.trim()}
        className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        Start Investigation
      </button>
    </form>
  );
}

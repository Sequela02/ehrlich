import { useState } from "react";
import { Key, Trash2 } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

const STORAGE_KEY = "ehrlich_api_key";

export function BYOKSettings() {
  const queryClient = useQueryClient();
  const [value, setValue] = useState("");
  const stored = localStorage.getItem(STORAGE_KEY);

  function handleSave() {
    const trimmed = value.trim();
    if (!trimmed) return;
    localStorage.setItem(STORAGE_KEY, trimmed);
    setValue("");
    void queryClient.invalidateQueries({ queryKey: ["credits"] });
  }

  function handleClear() {
    localStorage.removeItem(STORAGE_KEY);
    void queryClient.invalidateQueries({ queryKey: ["credits"] });
  }

  return (
    <div className="space-y-3 rounded-md border border-border bg-surface p-4">
      <div className="flex items-center gap-2">
        <Key className="h-4 w-4 text-muted-foreground" />
        <h3 className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Bring Your Own Key
        </h3>
      </div>

      {stored ? (
        <div className="flex items-center justify-between gap-3">
          <span className="font-mono text-xs text-primary">
            Using your own key (sk-...{stored.slice(-4)})
          </span>
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-1 rounded px-2 py-1 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
          >
            <Trash2 className="h-3 w-3" />
            Remove
          </button>
        </div>
      ) : (
        <div className="flex gap-2">
          <input
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="sk-ant-..."
            className="flex-1 rounded-sm border border-border bg-background px-3 py-1.5 font-mono text-xs placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
          <button
            onClick={handleSave}
            disabled={!value.trim()}
            className="rounded-sm bg-primary px-3 py-1.5 font-mono text-[11px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Save
          </button>
        </div>
      )}

      <p className="font-mono text-[10px] leading-relaxed text-muted-foreground/60">
        {stored
          ? "Investigations use your key directly. No platform credits consumed."
          : "Provide your Anthropic API key to bypass credit limits. Key is stored locally."}
      </p>
    </div>
  );
}

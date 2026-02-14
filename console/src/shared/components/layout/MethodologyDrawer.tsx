import { Link } from "@tanstack/react-router";
import { X, ArrowRight } from "lucide-react";
import { useMethodology } from "@/features/investigation/hooks/use-methodology";

interface MethodologyDrawerProps {
  open: boolean;
  onClose: () => void;
}

const MODEL_COLORS: Record<string, string> = {
  haiku: "text-secondary",
  opus: "text-primary",
  sonnet: "text-accent",
};

const MODEL_LABELS: Record<string, string> = {
  haiku: "Haiku",
  opus: "Opus",
  sonnet: "Sonnet",
};

export function MethodologyDrawer({ open, onClose }: MethodologyDrawerProps) {
  const { data } = useMethodology();

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 z-50 h-full w-[350px] transform border-l border-border bg-background transition-transform duration-200 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <span className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Methodology
            </span>
            <button
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 space-y-6 overflow-y-auto p-4">
            {data && (
              <>
                {/* Workflow phases */}
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                    6-Phase Workflow
                  </p>
                  <div className="mt-2 space-y-1.5">
                    {data.phases.map((phase) => (
                      <div
                        key={phase.number}
                        className="flex items-center gap-2 text-xs"
                      >
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-border font-mono text-[9px] text-muted-foreground">
                          {phase.number}
                        </span>
                        <span className="text-foreground/80">{phase.name}</span>
                        <span
                          className={`ml-auto font-mono text-[9px] ${MODEL_COLORS[phase.model]}`}
                        >
                          {MODEL_LABELS[phase.model]}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Models */}
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                    Model Architecture
                  </p>
                  <div className="mt-2 space-y-1">
                    {data.models.map((model) => (
                      <div
                        key={model.role}
                        className="flex items-center gap-2 text-xs"
                      >
                        <span className="font-medium text-foreground/80">
                          {model.role}
                        </span>
                        <span className="font-mono text-[9px] text-muted-foreground/50">
                          {model.model_id.split("-").slice(-1)[0]}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Domains */}
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                    Domains
                  </p>
                  <div className="mt-2 space-y-1">
                    {data.domains.map((domain) => (
                      <div
                        key={domain.name}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="text-foreground/80">
                          {domain.display_name}
                        </span>
                        <span className="font-mono text-[9px] text-muted-foreground/50">
                          {domain.tool_count} tools
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Data sources */}
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                    Data Sources
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {data.data_sources.length} APIs ({data.data_sources.filter((s) => s.url !== "internal").length} external + {data.data_sources.filter((s) => s.url === "internal").length} internal)
                  </p>
                </div>
              </>
            )}
          </div>

          <div className="border-t border-border p-4">
            <Link
              to="/methodology"
              onClick={onClose}
              className="flex items-center justify-center gap-2 rounded-sm border border-border bg-surface px-3 py-2 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
            >
              View full methodology
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}

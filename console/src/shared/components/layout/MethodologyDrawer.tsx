import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { useMethodology } from "@/features/investigation/hooks/use-methodology";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/shared/components/ui/sheet";

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
    <Sheet open={open} onOpenChange={(val) => !val && onClose()}>
      <SheetContent className="w-[350px] p-0 flex flex-col gap-0 sm:w-[400px]">
        <SheetHeader className="flex flex-row items-center justify-between space-y-0 px-4 py-3 border-b border-border bg-background">
          <SheetTitle className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Methodology
          </SheetTitle>
          <SheetDescription className="sr-only">
            Overview of the Ehrlich engine's 6-phase workflow, model architecture, and domain integration.
          </SheetDescription>
          {/* Close button is handled by SheetContent default X icon, but we need to ensure it doesn't overlap or look double. 
              The default X is absolute positioned right-4 top-4. 
              Our header is custom height. Let's see. 
              If we want the X in the header row, it's fine. 
          */}
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-4 py-6">
          {data && (
            <div className="space-y-6">
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
            </div>
          )}
        </div>

        <SheetFooter className="border-t border-border p-4 sm:justify-center">
          <Link
            to="/methodology"
            onClick={onClose}
            className="flex w-full items-center justify-center gap-2 rounded-sm border border-border bg-surface px-3 py-2 font-mono text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
          >
            View full methodology
            <ArrowRight className="h-3 w-3" />
          </Link>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

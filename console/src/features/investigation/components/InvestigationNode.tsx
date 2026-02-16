import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import {
    BrainCircuit,
    FlaskConical,
    FileText,
    Crosshair,
    Wrench,
    HelpCircle,
    Info,
    Search
} from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import type { InvestigationNodeData } from "../lib/diagram-builder";

// -- [CONSTANTS & DESCRIPTIONS] -------------------------------------------

const NODE_DESCRIPTIONS: Record<string, string> = {
    hypothesis: "A proposed explanation for a phenomenon. The AI generates these based on initial observations and refines them as evidence is gathered.",
    experiment: "A structured test designed to validate or refute a potential hypothesis. Executes specific tools (like Python or Search) to gather empirical evidence.",
    finding: "A discrete piece of evidence discovered during an experiment. It can either support, contradict, or be neutral towards a hypothesis.",
    root: "The central research goal or question that initiated this entire investigation."
};

// -- [COMPONENT] ----------------------------------------------------------

export function InvestigationNode({ data }: NodeProps<Node<InvestigationNodeData>>) {
    // Styles are passed pre-calculated in data for performance/consistency with layout engine
    // or we can re-derive them here. The builder passes stroke, fill, text.
    // However, the builder uses "status" to derive them.
    // Let's use the passed colors if available, or fallback.
    // The builder DOES pass stroke, fill, textColor.
    const { stroke, fill, textColor, type, label, sublabel, tool_count, confidence, rationale, detail } = data;

    // Custom gradient logic based on type
    let bgStyle = {
        backgroundColor: "var(--color-surface)",
        background: `linear-gradient(to bottom right, ${fill}, var(--color-surface))`
    };

    if (type === "root") {
        bgStyle = {
            backgroundColor: "var(--color-surface)",
            background: "var(--color-surface)"
        };
    }

    return (
        <TooltipProvider>
            <Tooltip delayDuration={300}>
                <TooltipTrigger asChild>
                    <div
                        className="flex flex-col items-center justify-center p-3 text-center transition-all hover:ring-2 hover:ring-primary/50 cursor-default"
                        style={{
                            width: 260,
                            height: 80,
                            borderRadius: "var(--radius-md)",
                            border: `2px solid ${stroke}`,
                            ...bgStyle,
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
                        }}
                    >
                        {/* 1. Default TOP Handle (Target for Vertical Flow) */}
                        <Handle type="target" position={Position.Top} className="!opacity-0" />

                        {type === "root" ? (
                            <div className="flex flex-col items-center">
                                <div className="flex items-center gap-1.5 mb-1 text-muted-foreground">
                                    <Crosshair className="w-3 h-3" />
                                    <span className="text-[10px] font-bold uppercase tracking-widest">RESEARCH GOAL</span>
                                </div>
                                <span className="text-sm font-semibold text-foreground leading-tight px-2">{label}</span>
                            </div>
                        ) : (
                            <>
                                <span
                                    className="line-clamp-2 w-full text-[13px] font-medium leading-tight px-1"
                                    style={{ color: "var(--color-foreground)" }}
                                >
                                    {label}
                                </span>
                                <div className="mt-2 flex items-center gap-2">
                                    <span
                                        className="font-mono text-[10px] font-bold uppercase tracking-wider"
                                        style={{ color: textColor }}
                                    >
                                        {sublabel}
                                    </span>
                                    {tool_count !== undefined && tool_count > 0 && (
                                        <span className="flex items-center gap-1 font-mono text-[9px] px-1.5 py-0.5 rounded bg-muted/50 text-muted-foreground" title="Tools used">
                                            <Wrench className="w-2.5 h-2.5" /> {tool_count}
                                        </span>
                                    )}
                                </div>
                            </>
                        )}

                        {/* 2. RIGHT Handle (Source for Side Findings) */}
                        <Handle type="source" id="right" position={Position.Right} className="!opacity-0" />

                        {/* 3. LEFT Handle (Target for Side Findings - Only Findings need this) */}
                        {type === "finding" && (
                            <Handle type="target" id="left" position={Position.Left} className="!opacity-0" />
                        )}

                        {/* 4. BOTTOM Handle (Source for Vertical Flow) */}
                        <Handle type="source" id="bottom" position={Position.Bottom} className="!opacity-0" />
                    </div>
                </TooltipTrigger>
                <TooltipContent className="max-w-[340px] p-0 overflow-hidden bg-popover border-border text-popover-foreground shadow-xl" side="right" sideOffset={10}>
                    <div className="px-3 py-2 border-b border-border bg-muted/30 flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                            {type === "hypothesis" && <BrainCircuit className="w-3.5 h-3.5" />}
                            {type === "experiment" && <FlaskConical className="w-3.5 h-3.5" />}
                            {type === "finding" && <FileText className="w-3.5 h-3.5" />}
                            {type === "root" && <Crosshair className="w-3.5 h-3.5" />}
                            {type.toUpperCase()}
                        </span>
                        {confidence !== undefined && (
                            <span className="text-xs font-mono text-muted-foreground">
                                Conf: <span className="text-foreground font-bold">{(confidence * 100).toFixed(0)}%</span>
                            </span>
                        )}
                    </div>

                    <div className="p-3 space-y-3">
                        {/* Educational Description */}
                        <div className="flex gap-2 text-[11px] leading-snug text-muted-foreground italic border-b border-border/40 pb-2">
                            <HelpCircle className="w-3 h-3 shrink-0 mt-0.5" />
                            {NODE_DESCRIPTIONS[type]}
                        </div>

                        <p className="text-sm font-medium leading-relaxed">{label}</p>

                        {rationale && (
                            <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded-md border border-border/50">
                                <span className="font-semibold text-foreground block mb-0.5 flex items-center gap-1.5">
                                    <Info className="w-3 h-3" /> Rationale
                                </span>
                                {rationale}
                            </div>
                        )}

                        {detail && (
                            <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded-md border border-border/50">
                                <span className="font-semibold text-foreground block mb-0.5 flex items-center gap-1.5">
                                    <Search className="w-3 h-3" /> Evidence Detail
                                </span>
                                {detail}
                            </div>
                        )}

                        {tool_count !== undefined && tool_count > 0 && (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1 border-t border-border/50 mt-2">
                                <Wrench className="w-3 h-3" />
                                <span> Executed {tool_count} automated tools</span>
                            </div>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}

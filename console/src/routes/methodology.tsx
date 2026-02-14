import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Database,
  FlaskConical,
  Globe,
  Layers,
  Lock,
  Wrench,
} from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { SectionHeader } from "@/shared/components/ui/SectionHeader";
import { useMethodology } from "@/features/investigation/hooks/use-methodology";
import type { Methodology } from "@/features/investigation/hooks/use-methodology";

export const Route = createFileRoute("/methodology")({
  component: MethodologyPage,
});

const MODEL_COLORS: Record<string, string> = {
  haiku: "text-secondary bg-secondary/10 border-secondary/20",
  opus: "text-primary bg-primary/10 border-primary/20",
  sonnet: "text-accent bg-accent/10 border-accent/20",
};

const MODEL_LABELS: Record<string, string> = {
  haiku: "Haiku",
  opus: "Opus",
  sonnet: "Sonnet",
};

function MethodologyPage() {
  const { data, isLoading } = useMethodology();

  if (isLoading || !data) {
    return (
      <div className="mx-auto max-w-[1200px] p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-64 rounded bg-muted" />
          <div className="h-4 w-96 rounded bg-muted/50" />
          <div className="h-32 rounded bg-muted/30" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1200px] space-y-12 p-8">
      <div className="space-y-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 font-mono text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          Back
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">How Ehrlich Works</h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          A hypothesis-driven scientific discovery engine that uses a multi-model
          architecture to formulate, test, and synthesize evidence across scientific
          domains.
        </p>
      </div>

      <WorkflowDiagram phases={data.phases} />
      <ModelArchitecture models={data.models} />
      <DomainRegistry domains={data.domains} />
      <ToolCatalog tools={data.tools} />
      <DataSources sources={data.data_sources} />
    </div>
  );
}

// ── 1. Workflow Diagram ──────────────────────────────────────────────────

function WorkflowDiagram({ phases }: { phases: Methodology["phases"] }) {
  const [expandedPhase, setExpandedPhase] = useState<number | null>(null);

  return (
    <section className="space-y-4">
      <SectionHeader
        icon={Layers}
        title="Investigation Workflow"
        description="Six sequential phases from question classification to evidence synthesis"
      />

      {/* Horizontal stepper */}
      <div className="overflow-x-auto rounded-md border border-border bg-surface p-6">
        <div className="flex min-w-[700px] items-start justify-between gap-1">
          {phases.map((phase, i) => (
            <div key={phase.number} className="flex items-start">
              <button
                onClick={() =>
                  setExpandedPhase(expandedPhase === phase.number ? null : phase.number)
                }
                className="group flex w-[100px] flex-col items-center gap-2"
              >
                <div
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-full border-2 font-mono text-sm font-semibold transition-colors",
                    expandedPhase === phase.number
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-muted-foreground group-hover:border-primary/50",
                  )}
                >
                  {phase.number}
                </div>
                <span className="text-center text-[10px] leading-tight text-muted-foreground">
                  {phase.name}
                </span>
                <span
                  className={cn(
                    "rounded-full border px-1.5 py-0.5 font-mono text-[9px] font-medium",
                    MODEL_COLORS[phase.model],
                  )}
                >
                  {MODEL_LABELS[phase.model]}
                </span>
              </button>
              {i < phases.length - 1 && (
                <div className="mt-4 h-px w-8 shrink-0 bg-border" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Expanded description */}
      {expandedPhase && (
        <div className="rounded-md border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-primary">
              Phase {expandedPhase}
            </span>
            <span className="text-sm font-medium">
              {phases.find((p) => p.number === expandedPhase)?.name}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {phases.find((p) => p.number === expandedPhase)?.description}
          </p>
        </div>
      )}
    </section>
  );
}

// ── 2. Model Architecture ────────────────────────────────────────────────

function ModelArchitecture({ models }: { models: Methodology["models"] }) {
  const roleColors: Record<string, string> = {
    Director: "text-primary",
    Researcher: "text-accent",
    Summarizer: "text-secondary",
  };

  return (
    <section className="space-y-4">
      <SectionHeader
        icon={FlaskConical}
        title="Multi-Model Architecture"
        description="Three specialized Claude models collaborate in a Director-Worker-Summarizer pattern"
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {models.map((model) => (
          <div
            key={model.role}
            className="rounded-md border border-border bg-surface p-4"
          >
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "text-sm font-semibold",
                  roleColors[model.role] ?? "text-foreground",
                )}
              >
                {model.role}
              </span>
            </div>
            <p className="mt-0.5 font-mono text-[10px] text-muted-foreground/60">
              {model.model_id}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              {model.purpose}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 3. Domain Registry ───────────────────────────────────────────────────

function DomainRegistry({ domains }: { domains: Methodology["domains"] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <section className="space-y-4">
      <SectionHeader
        icon={Globe}
        title="Domain Registry"
        description="Pluggable scientific domains with domain-specific tools, scoring, and visualization"
      />
      <div className="space-y-3">
        {domains.map((domain) => (
          <div
            key={domain.name}
            className="rounded-md border border-border bg-surface"
          >
            <button
              onClick={() =>
                setExpanded(expanded === domain.name ? null : domain.name)
              }
              className="flex w-full items-center justify-between p-4 text-left"
            >
              <div className="flex items-center gap-3">
                {expanded === domain.name ? (
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                )}
                <span className="text-sm font-medium">{domain.display_name}</span>
                <span className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground/70">
                  {domain.tool_count} tools
                </span>
              </div>
            </button>
            {expanded === domain.name && (
              <div className="border-t border-border px-4 pb-4 pt-3 text-xs">
                <div className="space-y-3">
                  {domain.score_definitions.length > 0 && (
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                        Score Definitions
                      </p>
                      <div className="mt-1.5 flex flex-wrap gap-2">
                        {domain.score_definitions.map((sd) => (
                          <span
                            key={sd.key}
                            className="rounded border border-border bg-muted/30 px-2 py-1 font-mono text-[10px]"
                          >
                            {sd.label}{" "}
                            <span className="text-muted-foreground/50">
                              ({sd.higher_is_better ? "higher better" : "lower better"})
                            </span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {domain.hypothesis_types.length > 0 && (
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                        Hypothesis Types
                      </p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {domain.hypothesis_types.map((ht) => (
                          <span
                            key={ht}
                            className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground"
                          >
                            {ht}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {domain.categories.length > 0 && (
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                        Domain Categories
                      </p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {domain.categories.map((cat) => (
                          <span
                            key={cat}
                            className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground"
                          >
                            {cat}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 4. Tool Catalog ──────────────────────────────────────────────────────

function ToolCatalog({ tools }: { tools: Methodology["tools"] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <section className="space-y-4">
      <SectionHeader
        icon={Wrench}
        title={`Tool Catalog (${tools.reduce((sum, g) => sum + g.tools.length, 0)})`}
        description="Domain-specific and universal tools available to the Researcher agent"
      />
      <div className="space-y-2">
        {tools.map((group) => (
          <div
            key={group.context}
            className="rounded-md border border-border bg-surface"
          >
            <button
              onClick={() =>
                setExpanded(expanded === group.context ? null : group.context)
              }
              className="flex w-full items-center justify-between p-3 text-left"
            >
              <div className="flex items-center gap-2">
                {expanded === group.context ? (
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                )}
                <span className="text-sm font-medium">{group.context}</span>
                <span className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground/70">
                  {group.tools.length}
                </span>
              </div>
            </button>
            {expanded === group.context && (
              <div className="border-t border-border px-3 pb-3 pt-2">
                <div className="space-y-1.5">
                  {group.tools.map((tool) => (
                    <div
                      key={tool.name}
                      className="flex items-start gap-2 rounded-md bg-muted/10 px-2.5 py-2"
                    >
                      <code className="shrink-0 font-mono text-[11px] text-primary">
                        {tool.name}
                      </code>
                      <span className="text-[11px] leading-relaxed text-muted-foreground">
                        {tool.description}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// ── 5. Data Sources ──────────────────────────────────────────────────────

function DataSources({ sources }: { sources: Methodology["data_sources"] }) {
  return (
    <section className="space-y-4">
      <SectionHeader
        icon={Database}
        title={`Data Sources (${sources.length})`}
        description="External APIs and internal indexes that power investigations"
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {sources.map((source) => (
          <div
            key={source.name}
            className="rounded-md border border-border bg-surface p-4"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{source.name}</span>
              {source.auth === "api_key" ? (
                <Lock className="h-3 w-3 text-accent" />
              ) : (
                <Globe className="h-3 w-3 text-primary" />
              )}
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground">
              {source.purpose}
            </p>
            <div className="mt-2 flex items-center gap-2">
              <span className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground/70">
                {source.context}
              </span>
              {source.url !== "internal" && (
                <span className="truncate font-mono text-[9px] text-muted-foreground/40">
                  {source.url.replace(/^https?:\/\//, "")}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}


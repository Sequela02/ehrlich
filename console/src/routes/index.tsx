import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronRight,
  Clock,
  FlaskConical,
  Key,
  LogIn,
  Sparkles,
} from "lucide-react";
import { PromptInput, InvestigationList, TemplateCards, BYOKSettings } from "@/features/investigation/components";
import { useInvestigations } from "@/features/investigation/hooks/use-investigations";
import { useStats } from "@/features/investigation/hooks/use-stats";
import { useAuth } from "@/shared/hooks/use-auth";
import { SectionHeader } from "@/shared/components/ui/SectionHeader";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: investigations } = useInvestigations();
  const { data: stats } = useStats();
  const { user, isLoading, signIn } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [byokOpen, setByokOpen] = useState(false);

  return (
    <div className="mx-auto max-w-[1200px] space-y-12 p-8">
      {/* Hero */}
      <div className="space-y-4 border-b border-border pb-10">
        <h1 className="text-4xl font-bold tracking-tight">Ehrlich</h1>
        <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
          A hypothesis-driven scientific discovery engine that uses a multi-model
          architecture to formulate, test, and synthesize evidence across
          scientific domains.
        </p>
        {stats && (
          <div className="flex items-center gap-4">
            <Link
              to="/methodology"
              className="inline-flex items-center gap-3 font-mono text-xs text-muted-foreground/70 transition-colors hover:text-foreground"
            >
              <span>{stats.tool_count} tools</span>
              <span className="text-border">{"\u00b7"}</span>
              <span>{stats.phase_count} phases</span>
              <span className="text-border">{"\u00b7"}</span>
              <span>{stats.domain_count} domains</span>
              <span className="text-border">{"\u00b7"}</span>
              <span>{stats.data_source_count} data sources</span>
            </Link>
          </div>
        )}
      </div>

      {/* Prompt or Sign-in */}
      {!isLoading && !user ? (
        <div className="flex flex-col items-center gap-4 rounded-md border border-border bg-surface px-8 py-12">
          <LogIn className="h-6 w-6 text-muted-foreground" />
          <div className="text-center">
            <p className="text-sm font-medium">Sign in to start an investigation</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Use your account to run AI-powered scientific investigations
            </p>
          </div>
          <button
            onClick={() => signIn()}
            className="mt-2 inline-flex items-center gap-2 rounded-sm bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            Sign in
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <PromptInput value={prompt} onChange={setPrompt} />

          {/* BYOK toggle */}
          <div>
            <button
              onClick={() => setByokOpen((p) => !p)}
              className="inline-flex items-center gap-1.5 font-mono text-[11px] text-muted-foreground/70 transition-colors hover:text-foreground"
            >
              {byokOpen ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              <Key className="h-3 w-3" />
              Bring Your Own Key
            </button>
            {byokOpen && (
              <div className="mt-2">
                <BYOKSettings />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Research Templates */}
      <section className="space-y-4">
        <SectionHeader
          icon={Sparkles}
          title="Research Templates"
          description="Pre-built prompts across molecular, training, and nutrition science domains"
        />
        <TemplateCards onSelect={setPrompt} />
      </section>

      {/* Recent Investigations */}
      {investigations && investigations.length > 0 && (
        <section className="space-y-4">
          <SectionHeader
            icon={Clock}
            title="Recent Investigations"
            description="Past investigations with full audit trails and structured reports"
          />
          <InvestigationList investigations={investigations} />
        </section>
      )}

      {/* Empty state for new users */}
      {investigations && investigations.length === 0 && user && (
        <section className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border py-12">
          <FlaskConical className="h-6 w-6 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            No investigations yet. Start one above or use a template.
          </p>
        </section>
      )}
    </div>
  );
}

import { motion } from "motion/react";
import { Database, Globe } from "lucide-react";
import { DATA_SOURCES } from "@/lib/constants";

function SourceCard({ source, index }: { source: (typeof DATA_SOURCES)[number]; index: number }) {
  const isInternal = source.access === "Internal";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.04, duration: 0.4 }}
      className={`group relative flex items-start gap-4 p-4 bg-surface/30 border rounded transition-all hover:bg-surface/60 ${
        isInternal
          ? "border-primary/30 hover:border-primary/60"
          : "border-border hover:border-primary/50"
      }`}
    >
      <div className="p-2 bg-background rounded border border-border/50 group-hover:border-primary/30 transition-colors shrink-0">
        <Database size={14} className="text-muted-foreground group-hover:text-primary transition-colors" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="font-bold text-sm text-foreground/90 group-hover:text-primary transition-colors">
            {source.name}
          </span>
          {isInternal && (
            <span className="font-mono text-[9px] text-primary bg-primary/10 px-1.5 py-0.5 rounded uppercase">
              Self-referential
            </span>
          )}
        </div>
        <div className="text-[11px] text-muted-foreground leading-relaxed">
          {source.purpose}
        </div>
        <div className="flex items-center gap-3 mt-1.5 font-mono text-[10px] text-muted-foreground/50">
          <span>{source.records}</span>
          <span className="text-border">&middot;</span>
          <span>{source.access}</span>
        </div>
      </div>
    </motion.div>
  );
}

export function DataSources() {
  return (
    <section id="data-sources" className="relative py-32 px-4 lg:px-0 border-t border-border/30">

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid lg:grid-cols-3 gap-16">

          {/* Header Content */}
          <div className="lg:col-span-1 space-y-8">
            <div>
              <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 rounded-full border border-border bg-surface/50 backdrop-blur-sm">
                <Globe size={14} className="text-primary" />
                <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Ground Truth</span>
              </div>
              <h2 className="text-4xl font-bold tracking-tight mb-4 text-foreground">
                Every claim<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
                  has a source.
                </span>
              </h2>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Ehrlich queries trusted global databases in real time. Findings link
                to ChEMBL compound IDs, PDB structure codes, DOIs, and PubChem CIDs.
                No hallucinated citations. No invented data points.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-surface/20 border border-border/50">
                <div className="text-3xl font-mono font-bold text-primary mb-1">15</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider">External APIs</div>
              </div>
              <div className="p-4 rounded-lg bg-surface/20 border border-border/50">
                <div className="text-3xl font-mono font-bold text-secondary mb-1">+1</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider">Institutional Memory</div>
              </div>
            </div>

            {/* Institutional memory callout */}
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <h4 className="font-mono text-[10px] text-primary uppercase tracking-wider mb-2">
                Self-Referential Research
              </h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every investigation&apos;s findings are indexed in a full-text search database.
                Future investigations query past findings via{" "}
                <code className="font-mono text-[10px] text-primary">search_prior_research</code>.
                Knowledge compounds over time.
              </p>
            </div>
          </div>

          {/* Grid of Sources */}
          <div className="lg:col-span-2">
            <div className="grid md:grid-cols-2 gap-3">
              {DATA_SOURCES.map((source, i) => (
                <SourceCard key={source.name} source={source} index={i} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

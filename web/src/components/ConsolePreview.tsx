import { motion, useReducedMotion } from "motion/react";
import { SectionHeader } from "./SectionHeader";

/* ── Static data for mockups ──────────────────────────────────── */

const HYPOTHESES = [
  { id: "H1", statement: "Compound X MIC < 4 µg/mL against MRSA", status: "supported" as const, confidence: 0.89 },
  { id: "H2", statement: "Resistance risk via efflux pump mutations is low", status: "refuted" as const, confidence: 0.23 },
  { id: "H3", statement: "ADMET profile permits oral bioavailability", status: "testing" as const, confidence: 0.65 },
] as const;

const CANDIDATES = [
  { id: "CMP-1247", score: 0.94, docking: -8.7, admet: "Pass", lipinski: true },
  { id: "CMP-0893", score: 0.87, docking: -7.9, admet: "Pass", lipinski: true },
  { id: "CMP-2156", score: 0.81, docking: -7.2, admet: "Warn", lipinski: true },
  { id: "CMP-0412", score: 0.74, docking: -6.8, admet: "Pass", lipinski: false },
] as const;

const TIMELINE_EVENTS: ReadonlyArray<{ phase: string; event: string; time: string; highlight?: boolean }> = [
  { phase: "PICO", event: "Domain detected: Molecular Science", time: "0.8s" },
  { phase: "LIT", event: "23 papers found via Semantic Scholar", time: "3.2s" },
  { phase: "LIT", event: "GRADE assessment: moderate certainty", time: "4.1s" },
  { phase: "FORM", event: "3 hypotheses formulated (Opus)", time: "8.4s" },
  { phase: "FORM", event: "Awaiting approval...", time: "8.5s", highlight: true },
  { phase: "TEST", event: "ChEMBL screen → 47 candidates", time: "12.3s" },
  { phase: "TEST", event: "AutoDock Vina → 12 binding hits", time: "18.7s" },
  { phase: "TEST", event: "XGBoost trained (scaffold-split AUC: 0.84)", time: "22.1s" },
  { phase: "CTRL", event: "Z'-factor: 0.72 (excellent)", time: "25.6s" },
  { phase: "SYNTH", event: "GRADE synthesis: ⊕⊕⊕⊖ moderate", time: "30.2s" },
];

const PHASE_COLORS: Record<string, string> = {
  PICO: "text-accent",
  LIT: "text-secondary",
  FORM: "text-primary",
  TEST: "text-primary",
  CTRL: "text-accent",
  SYNTH: "text-secondary",
};

const STATUS_STYLES = {
  supported: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", label: "SUPPORTED" },
  refuted: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", label: "REFUTED" },
  testing: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400", label: "TESTING" },
} as const;

/* ── Browser frame wrapper ────────────────────────────────────── */

function BrowserFrame({
  title,
  url,
  children,
}: {
  title: string;
  url: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg overflow-hidden border border-border bg-background shadow-2xl shadow-black/40">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-surface border-b border-border">
        <div className="flex gap-1.5">
          <span className="w-3 h-3 rounded-full bg-destructive/60" />
          <span className="w-3 h-3 rounded-full bg-accent/60" />
          <span className="w-3 h-3 rounded-full bg-primary/60" />
        </div>
        <div className="flex-1 flex justify-center">
          <div className="flex items-center gap-2 bg-background/60 border border-border/50 rounded px-3 py-1 max-w-sm w-full">
            <svg width="10" height="10" viewBox="0 0 10 10" className="text-muted-foreground/40 shrink-0">
              <circle cx="5" cy="5" r="4" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span className="font-mono text-[10px] text-muted-foreground/50 truncate">
              {url}
            </span>
          </div>
        </div>
        <span className="font-mono text-[9px] text-muted-foreground/30 uppercase tracking-wider shrink-0">
          {title}
        </span>
      </div>
      {/* Content */}
      <div className="p-5 bg-background">
        {children}
      </div>
    </div>
  );
}

/* ── Mockup components ────────────────────────────────────────── */

function HypothesisBoard() {
  return (
    <div className="space-y-3">
      <span className="font-mono text-[10px] text-muted-foreground/40 uppercase tracking-wider">
        Hypothesis Board
      </span>
      <div className="space-y-2">
        {HYPOTHESES.map((h) => {
          const s = STATUS_STYLES[h.status];
          return (
            <div
              key={h.id}
              className={`${s.bg} border ${s.border} rounded-sm p-3`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] text-foreground/60">{h.id}</span>
                <span className={`font-mono text-[9px] ${s.text} uppercase tracking-wider`}>
                  {s.label}
                </span>
              </div>
              <p className="font-mono text-[11px] text-foreground/80 leading-relaxed mb-2">
                {h.statement}
              </p>
              {/* Confidence bar */}
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 bg-black/30 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${h.status === "refuted" ? "bg-red-500/60" : h.status === "supported" ? "bg-green-500/60" : "bg-blue-500/60"}`}
                    style={{ width: `${h.confidence * 100}%` }}
                  />
                </div>
                <span className="font-mono text-[9px] text-muted-foreground/50">
                  {h.confidence.toFixed(2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CandidateTable() {
  return (
    <div className="space-y-3">
      <span className="font-mono text-[10px] text-muted-foreground/40 uppercase tracking-wider">
        Candidate Ranking
      </span>
      <div className="border border-border rounded-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-surface/30">
              <th className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-wider text-left px-3 py-2">ID</th>
              <th className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-wider text-right px-3 py-2">Score</th>
              <th className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-wider text-right px-3 py-2">Docking</th>
              <th className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-wider text-center px-3 py-2">ADMET</th>
              <th className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-wider text-center px-3 py-2">Lipinski</th>
            </tr>
          </thead>
          <tbody>
            {CANDIDATES.map((c, i) => (
              <tr
                key={c.id}
                className={`border-b border-border/30 ${i === 0 ? "bg-primary/5" : ""}`}
              >
                <td className="font-mono text-[11px] text-foreground/80 px-3 py-2">{c.id}</td>
                <td className={`font-mono text-[11px] text-right px-3 py-2 ${c.score >= 0.9 ? "text-green-400" : c.score >= 0.8 ? "text-primary" : "text-accent"}`}>
                  {c.score.toFixed(2)}
                </td>
                <td className="font-mono text-[11px] text-secondary text-right px-3 py-2">
                  {c.docking.toFixed(1)} kcal
                </td>
                <td className="text-center px-3 py-2">
                  <span className={`font-mono text-[9px] px-1.5 py-0.5 rounded ${c.admet === "Pass" ? "text-green-400 bg-green-500/10" : "text-accent bg-accent/10"}`}>
                    {c.admet}
                  </span>
                </td>
                <td className="text-center px-3 py-2">
                  <span className={`font-mono text-[9px] ${c.lipinski ? "text-green-400" : "text-red-400"}`}>
                    {c.lipinski ? "5/5" : "4/5"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function InvestigationTimeline() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-muted-foreground/40 uppercase tracking-wider">
          Investigation Timeline
        </span>
        <span className="font-mono text-[10px] text-muted-foreground/30">
          ~30s total
        </span>
      </div>

      {/* Phase progress bar */}
      <div className="flex gap-1">
        {["PICO", "LIT", "FORM", "TEST", "CTRL", "SYNTH"].map((phase, i) => (
          <div key={phase} className="flex-1 flex flex-col items-center gap-1">
            <div className={`w-full h-1.5 rounded-full ${i < 5 ? "bg-primary/40" : "bg-primary/20"}`} />
            <span className="font-mono text-[8px] text-muted-foreground/30">{phase}</span>
          </div>
        ))}
      </div>

      {/* Event list */}
      <div className="space-y-0.5 max-h-[280px] overflow-hidden">
        {TIMELINE_EVENTS.map((evt, i) => (
          <div
            key={i}
            className={`flex items-start gap-2 py-1 ${evt.highlight ? "bg-accent/5 rounded px-1.5 -mx-1.5" : ""}`}
          >
            <span className={`font-mono text-[9px] w-10 shrink-0 ${PHASE_COLORS[evt.phase] ?? "text-muted-foreground"}`}>
              [{evt.phase}]
            </span>
            <span className={`font-mono text-[10px] flex-1 ${evt.highlight ? "text-accent" : "text-muted-foreground/60"}`}>
              {evt.event}
            </span>
            <span className="font-mono text-[9px] text-muted-foreground/30 shrink-0">
              {evt.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniRadarChart() {
  const axes = ["Absorption", "Metabolism", "Toxicity", "Solubility", "Permeability", "Stability"];
  const values = [0.85, 0.72, 0.91, 0.68, 0.79, 0.88];
  const cx = 80, cy = 80, r = 60;

  const points = values.map((v, i) => {
    const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
    return {
      x: cx + r * v * Math.cos(angle),
      y: cy + r * v * Math.sin(angle),
      lx: cx + (r + 14) * Math.cos(angle),
      ly: cy + (r + 14) * Math.sin(angle),
      label: axes[i],
    };
  });

  const polygonPoints = points.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="space-y-3">
      <span className="font-mono text-[10px] text-muted-foreground/40 uppercase tracking-wider">
        ADMET Radar
      </span>
      <div className="flex justify-center">
        <svg width="160" height="160" viewBox="0 0 160 160">
          {/* Grid rings */}
          {[0.25, 0.5, 0.75, 1].map((scale) => (
            <polygon
              key={scale}
              points={axes.map((_, i) => {
                const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
                return `${cx + r * scale * Math.cos(angle)},${cy + r * scale * Math.sin(angle)}`;
              }).join(" ")}
              fill="none"
              stroke="oklch(0.22 0.01 155)"
              strokeWidth="0.5"
            />
          ))}
          {/* Axes */}
          {axes.map((_, i) => {
            const angle = (Math.PI * 2 * i) / axes.length - Math.PI / 2;
            return (
              <line
                key={i}
                x1={cx} y1={cy}
                x2={cx + r * Math.cos(angle)}
                y2={cy + r * Math.sin(angle)}
                stroke="oklch(0.22 0.01 155)"
                strokeWidth="0.5"
              />
            );
          })}
          {/* Data polygon */}
          <polygon
            points={polygonPoints}
            fill="oklch(0.72 0.19 155 / 0.15)"
            stroke="oklch(0.72 0.19 155)"
            strokeWidth="1.5"
          />
          {/* Data points */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="2" fill="oklch(0.72 0.19 155)" />
          ))}
          {/* Labels */}
          {points.map((p, i) => (
            <text
              key={`label-${i}`}
              x={p.lx}
              y={p.ly}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-muted-foreground/40"
              style={{ fontSize: "6px", fontFamily: "var(--font-mono)" }}
            >
              {p.label}
            </text>
          ))}
        </svg>
      </div>
    </div>
  );
}

/* ── Main section ─────────────────────────────────────────────── */

export function ConsolePreview() {
  const reduced = useReducedMotion();

  return (
    <section className="py-24 px-4 lg:px-0 max-w-[1200px] mx-auto border-t border-border">
      <SectionHeader title="Console" />

      <div className="mb-12 max-w-2xl">
        <h3 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground mb-4">
          What you see while it runs.
        </h3>
        <p className="text-base text-muted-foreground leading-relaxed">
          SSE events stream into the console in real time. Hypotheses update live.
          Candidates rank as experiments complete. Charts render when visualization
          tools fire. You approve hypotheses before testing begins.
        </p>
      </div>

      <motion.div
        initial={reduced ? false : { opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="space-y-6"
      >
        {/* Main mockup: Timeline + Hypothesis Board side by side in browser frame */}
        <BrowserFrame
          title="Investigation"
          url="localhost:5173/investigation/inv_8f3a2b"
        >
          {/* Investigation prompt */}
          <div className="mb-5 pb-4 border-b border-border/50">
            <span className="font-mono text-[9px] text-muted-foreground/40 uppercase tracking-wider block mb-1.5">
              Research Question
            </span>
            <p className="font-mono text-sm text-foreground/90 leading-relaxed">
              Find antimicrobial compounds effective against MRSA with low resistance risk and favorable ADMET profiles
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InvestigationTimeline />
            <HypothesisBoard />
          </div>
        </BrowserFrame>

        {/* Second row: Candidates + Radar in separate browser frames */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <BrowserFrame
            title="Candidates"
            url="localhost:5173/investigation/inv_8f3a2b#candidates"
          >
            <CandidateTable />
          </BrowserFrame>

          <BrowserFrame
            title="ADMET Profile"
            url="localhost:5173/investigation/inv_8f3a2b#admet"
          >
            <MiniRadarChart />
          </BrowserFrame>
        </div>
      </motion.div>
    </section>
  );
}

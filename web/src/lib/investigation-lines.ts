export type LineVariant =
  | "command"
  | "query"
  | "phase"
  | "hypothesis"
  | "tool"
  | "finding"
  | "status"
  | "blank";

export interface TerminalLine {
  text: string;
  variant: LineVariant;
  delay: number;
}

export const INVESTIGATION_LINES: TerminalLine[] = [
  { text: "$ ehrlich investigate", variant: "command", delay: 0 },
  {
    text: '> "Compare polarized vs HIIT training for VO2max improvement"',
    variant: "query",
    delay: 800,
  },
  { text: "", variant: "blank", delay: 400 },
  {
    text: "PHASE 1 \u25B8 Classification & PICO                    2.1s",
    variant: "phase",
    delay: 600,
  },
  {
    text: "PHASE 2 \u25B8 Literature Survey                        4.8s",
    variant: "phase",
    delay: 500,
  },
  {
    text: "PHASE 3 \u25B8 Hypothesis Formulation                   3.2s",
    variant: "phase",
    delay: 500,
  },
  { text: "", variant: "blank", delay: 300 },
  {
    text: "  H1: Polarized training yields >5% VO2max gain     prior: 0.70",
    variant: "hypothesis",
    delay: 700,
  },
  {
    text: "  H2: HIIT at 90% HRmax outperforms steady-state    prior: 0.60",
    variant: "hypothesis",
    delay: 500,
  },
  { text: "", variant: "blank", delay: 300 },
  { text: "PHASE 4 \u25B8 Experiment Testing", variant: "phase", delay: 400 },
  {
    text: '  \u251C\u2500 search_training_literature(query="VO2max polarized")',
    variant: "tool",
    delay: 400,
  },
  {
    text: "  \u251C\u2500 analyze_training_evidence(studies=[12 RCTs])",
    variant: "tool",
    delay: 350,
  },
  {
    text: '  \u251C\u2500 compare_protocols(a="polarized", b="HIIT")',
    variant: "tool",
    delay: 350,
  },
  {
    text: '  \u2514\u2500 search_clinical_trials(condition="VO2max")',
    variant: "tool",
    delay: 350,
  },
  { text: "", variant: "blank", delay: 500 },
  {
    text: "PHASE 5 \u25B8 Negative Controls                        1.4s",
    variant: "phase",
    delay: 400,
  },
  { text: "", variant: "blank", delay: 300 },
  {
    text: "  FINDING: Polarized training +6.8% (95% CI: 4.2\u20139.4%)",
    variant: "finding",
    delay: 800,
  },
  {
    text: "  H1 \u25B8 SUPPORTED    confidence: 0.85    evidence: MODERATE",
    variant: "status",
    delay: 600,
  },
];

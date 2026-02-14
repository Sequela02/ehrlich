import { FlaskConical, Brain, Leaf, Target, Activity, Shield, Apple } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Template {
  title: string;
  domain: string;
  domainTag: string;
  prompt: string;
  Icon: LucideIcon;
}

const TEMPLATES: Template[] = [
  {
    title: "MRSA Antimicrobials",
    domain: "Antimicrobial Resistance",
    domainTag: "Molecular Science",
    prompt:
      "Find novel antimicrobial candidates against MRSA (methicillin-resistant Staphylococcus aureus). Focus on compounds that can bypass the PBP2a resistance mechanism, with drug-like ADMET properties and low resistance risk.",
    Icon: FlaskConical,
  },
  {
    title: "Alzheimer's Drug Candidates",
    domain: "Neurodegenerative Disease",
    domainTag: "Molecular Science",
    prompt:
      "Identify potential drug candidates for Alzheimer's disease targeting amyloid-beta aggregation and tau phosphorylation. Prioritize blood-brain barrier permeable compounds with favorable safety profiles.",
    Icon: Brain,
  },
  {
    title: "Environmental Toxicity Screen",
    domain: "Environmental Science",
    domainTag: "Molecular Science",
    prompt:
      "Screen common industrial solvents for environmental toxicity, bioaccumulation potential, and aquatic organism effects. Identify safer alternatives with similar functional properties.",
    Icon: Leaf,
  },
  {
    title: "Cancer Kinase Inhibitors",
    domain: "Oncology",
    domainTag: "Molecular Science",
    prompt:
      "Discover selective kinase inhibitor candidates for non-small cell lung cancer targeting EGFR T790M mutation. Evaluate binding affinity, selectivity over wild-type EGFR, and drug-likeness.",
    Icon: Target,
  },
  {
    title: "VO2max Training Optimization",
    domain: "Exercise Physiology",
    domainTag: "Training Science",
    prompt:
      "What are the most effective training protocols for improving VO2max in recreational runners? Compare high-intensity interval training (HIIT) vs polarized training vs threshold training, considering evidence quality, effect sizes, and injury risk.",
    Icon: Activity,
  },
  {
    title: "ACL Injury Prevention",
    domain: "Sports Medicine",
    domainTag: "Training Science",
    prompt:
      "Evaluate evidence-based neuromuscular training programs for ACL injury prevention in female soccer players. Analyze which exercise components (plyometrics, balance, strength) have the strongest protective effect and optimal training frequency.",
    Icon: Shield,
  },
  {
    title: "Creatine for Strength",
    domain: "Sports Nutrition",
    domainTag: "Nutrition Science",
    prompt:
      "What is the evidence for creatine monohydrate supplementation on strength and power performance? Analyze dosing protocols, loading phases, and safety profile from meta-analyses.",
    Icon: Apple,
  },
];

interface TemplateCardsProps {
  onSelect: (prompt: string) => void;
}

export function TemplateCards({ onSelect }: TemplateCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {TEMPLATES.map((template) => (
        <button
          key={template.title}
          onClick={() => onSelect(template.prompt)}
          className="group rounded-sm border border-border bg-surface p-4 text-left transition-all hover:border-primary/30 hover:bg-primary/5"
        >
          <div className="flex items-start gap-3">
            <template.Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-foreground">
                  {template.title}
                </p>
                <span className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-muted-foreground/70">
                  {template.domainTag}
                </span>
              </div>
              <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/60">
                {template.domain}
              </p>
              <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                {template.prompt}
              </p>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

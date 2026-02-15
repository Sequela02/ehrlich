import { useState, useMemo } from "react";
import { FlaskConical, Brain, Leaf, Target, Activity, Shield, Apple, Scale, HeartPulse, Search } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
// import { Badge } from "@/shared/components/ui/badge"; // Fallback to button if badge not present, but using button is safer for interactive elements

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
  {
    title: "CCT School Enrollment",
    domain: "Education Policy",
    domainTag: "Impact Evaluation",
    prompt:
      "What is the causal effect of conditional cash transfer programs on school enrollment and attendance in Latin America? Compare Prospera (Mexico), Bolsa Familia (Brazil), and Familias en Accion (Colombia) using available outcome data.",
    Icon: Scale,
  },
  {
    title: "Health Worker Programs",
    domain: "Health Policy",
    domainTag: "Impact Evaluation",
    prompt:
      "Evaluate the impact of community health worker programs on maternal mortality and childhood vaccination rates in sub-Saharan Africa. Use WHO and World Bank indicators.",
    Icon: HeartPulse,
  },
];

interface TemplateCardsProps {
  onSelect: (prompt: string) => void;
  limit?: number;
}

export function TemplateCards({ onSelect, limit }: TemplateCardsProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const displayedTemplates = limit ? TEMPLATES.slice(0, limit) : TEMPLATES;

  const uniqueTags = useMemo(() => {
    return Array.from(new Set(TEMPLATES.map((t) => t.domainTag)));
  }, []);

  const filteredTemplates = useMemo(() => {
    return TEMPLATES.filter((t) => {
      const matchesSearch =
        t.title.toLowerCase().includes(search.toLowerCase()) ||
        t.prompt.toLowerCase().includes(search.toLowerCase()) ||
        t.domain.toLowerCase().includes(search.toLowerCase());
      const matchesTag = selectedTag ? t.domainTag === selectedTag : true;
      return matchesSearch && matchesTag;
    });
  }, [search, selectedTag]);

  const renderTemplate = (template: Template) => (
    <button
      key={template.title}
      onClick={() => {
        onSelect(template.prompt);
        setOpen(false);
      }}
      className="group flex flex-col items-start gap-2 rounded-lg border border-border bg-surface p-4 text-left transition-all hover:border-primary/50 hover:shadow-sm"
      aria-label={`Select template: ${template.title}`}
    >
      <div className="flex w-full items-start justify-between">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
          <template.Icon className="h-4 w-4" />
        </div>
        <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
          {template.domainTag}
        </span>
      </div>
      <div>
        <div className="font-medium text-foreground">{template.title}</div>
        <div className="mt-1 text-xs text-muted-foreground line-clamp-2">
          {template.prompt}
        </div>
      </div>
    </button>
  );

  return (
    <div className="space-y-4">
      {/* Home Page Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {displayedTemplates.map((t) => (
          <button
            key={t.title}
            onClick={() => onSelect(t.prompt)}
            className="group flex flex-col items-start gap-2 rounded-lg border border-border bg-surface p-4 text-left transition-all hover:border-primary/50 hover:shadow-sm"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
              <t.Icon className="h-4 w-4" />
            </div>
            <div>
              <div className="font-medium text-foreground">{t.title}</div>
              <div className="mt-1 text-xs text-muted-foreground line-clamp-2">
                {t.prompt}
              </div>
            </div>
          </button>
        ))}
      </div>

      {limit && limit < TEMPLATES.length && (
        <div className="flex justify-center">
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                Show all {TEMPLATES.length} templates
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
              <DialogHeader>
                <DialogTitle>Research Templates</DialogTitle>
                <DialogDescription>
                  Choose a pre-defined prompt to start your investigation.
                </DialogDescription>
              </DialogHeader>

              <div className="flex flex-col gap-4 py-4 border-b border-border">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search templates..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>

                {/* Filter Tags */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={selectedTag === null ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => setSelectedTag(null)}
                    className="h-7 text-xs"
                  >
                    All
                  </Button>
                  {uniqueTags.map((tag) => (
                    <Button
                      key={tag}
                      variant={selectedTag === tag ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setSelectedTag(tag)}
                      className="h-7 text-xs"
                    >
                      {tag}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex-1 overflow-y-auto py-4">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredTemplates.length > 0 ? (
                    filteredTemplates.map(renderTemplate)
                  ) : (
                    <div className="col-span-full py-8 text-center text-muted-foreground">
                      No templates found matching your criteria.
                    </div>
                  )}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      )}
    </div>
  );
}

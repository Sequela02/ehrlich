import { ExternalLink, FileText } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { Finding } from "../types";

interface FindingsPanelProps {
  findings: Finding[];
}

const EVIDENCE_COLORS: Record<string, string> = {
  supporting: "bg-secondary/20 text-secondary",
  contradicting: "bg-destructive/20 text-destructive",
  neutral: "bg-muted text-muted-foreground",
};

const SOURCE_URLS: Record<string, (id: string) => string> = {
  chembl: (id) => `https://www.ebi.ac.uk/chembl/compound_report_card/${id}`,
  pdb: (id) => `https://www.rcsb.org/structure/${id}`,
  doi: (id) => `https://doi.org/${id}`,
  pubchem: (id) => `https://pubchem.ncbi.nlm.nih.gov/compound/${id}`,
  uniprot: (id) => `https://www.uniprot.org/uniprotkb/${id}`,
  opentargets: (id) => `https://platform.opentargets.org/target/${id}`,
  gtopdb: (id) => `https://www.guidetopharmacology.org/GRAC/LigandDisplayForward?ligandId=${id}`,
  ehrlich: (id) => `/investigation/${id}`,
};

const SOURCE_LABELS: Record<string, string> = {
  chembl: "ChEMBL",
  pdb: "PDB",
  doi: "DOI",
  pubchem: "PubChem",
  uniprot: "UniProt",
  opentargets: "Open Targets",
  gtopdb: "GtoPdb",
  ehrlich: "Ehrlich",
};

export function FindingsPanel({ findings }: FindingsPanelProps) {
  const grouped = findings.reduce<Record<string, Finding[]>>((acc, f) => {
    const key = f.hypothesis_id || "general";
    if (!acc[key]) acc[key] = [];
    acc[key].push(f);
    return acc;
  }, {});

  const groups = Object.entries(grouped);

  return (
    <div className="space-y-3">
      <div>
        <h3 className="border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
          Findings{findings.length > 0 && ` (${findings.length})`}
        </h3>
        <p className="mt-1 pl-4 text-xs leading-relaxed text-muted-foreground/50">
          Evidence collected during experiments, linked to hypotheses and classified as supporting, contradicting, or neutral.
        </p>
      </div>
      {findings.length === 0 ? (
        <p className="px-1 text-xs text-muted-foreground/50">
          Findings will appear as the investigation progresses.
        </p>
      ) : (
        <div className="max-h-[400px] overflow-y-auto">
          <div className="space-y-4">
            {groups.map(([hypothesisId, groupFindings]) => (
              <div key={hypothesisId}>
                {groups.length > 1 && (
                  <p className="mb-2 font-mono text-[10px] uppercase text-muted-foreground/60">
                    {hypothesisId === "general"
                      ? "General"
                      : `Hypothesis ${hypothesisId.slice(0, 8)}`}
                  </p>
                )}
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {groupFindings.map((f, i) => (
                    <div
                      key={i}
                      className="rounded-md border border-border bg-surface p-3"
                    >
                      <div className="flex items-start gap-2">
                        <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        <div className="min-w-0">
                          <p className="text-xs font-medium">{f.title}</p>
                          <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
                            <span
                              className={cn(
                                "inline-block rounded px-1.5 py-0.5 font-mono text-[10px]",
                                EVIDENCE_COLORS[f.evidence_type] ?? EVIDENCE_COLORS.neutral,
                              )}
                            >
                              {f.evidence_type}
                            </span>
                            <SourceBadge sourceType={f.source_type} sourceId={f.source_id} />
                          </div>
                          {f.detail && (
                            <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                              {f.detail}
                            </p>
                          )}
                          {f.evidence && (
                            <div className="mt-2 rounded bg-muted/30 px-2 py-1.5">
                              <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
                                Evidence
                              </span>
                              <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                                {f.evidence}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SourceBadge({ sourceType, sourceId }: { sourceType?: string; sourceId?: string }) {
  if (!sourceType || !sourceId) return null;

  const label = SOURCE_LABELS[sourceType] ?? sourceType;
  const urlBuilder = SOURCE_URLS[sourceType];
  const url = urlBuilder ? urlBuilder(sourceId) : undefined;
  const isInternal = sourceType === "ehrlich";

  if (url) {
    return (
      <a
        href={url}
        target={isInternal ? undefined : "_blank"}
        rel={isInternal ? undefined : "noopener noreferrer"}
        className="inline-flex items-center gap-1 rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] text-primary transition-colors hover:bg-primary/20"
      >
        {label} {sourceId.slice(0, 8)}
        {!isInternal && <ExternalLink className="h-2.5 w-2.5" />}
      </a>
    );
  }

  return (
    <span className="inline-block rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
      {label} {sourceId}
    </span>
  );
}

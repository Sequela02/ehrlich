import { useEffect, useState } from "react";

import { MolViewer2D } from "@/features/molecule/components/MolViewer2D";
import { MolViewer3D } from "@/features/molecule/components/MolViewer3D";
import { apiFetch } from "@/shared/lib/api";

interface ConformerData {
  mol_block: string;
  energy: number;
  num_atoms: number;
}

interface DescriptorData {
  molecular_weight: number;
  logp: number;
  tpsa: number;
  hbd: number;
  hba: number;
  rotatable_bonds: number;
  qed: number;
  num_rings: number;
  passes_lipinski: boolean;
}

interface CandidateDetailProps {
  smiles: string;
  name: string;
}

export function CandidateDetail({ smiles, name }: CandidateDetailProps) {
  const [conformer, setConformer] = useState<ConformerData | null>(null);
  const [descriptors, setDescriptors] = useState<DescriptorData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const encoded = encodeURIComponent(smiles);

    Promise.all([
      apiFetch<ConformerData>(`/molecule/conformer?smiles=${encoded}`).catch(() => null),
      apiFetch<DescriptorData>(`/molecule/descriptors?smiles=${encoded}`).catch(() => null),
    ]).then(([conf, desc]) => {
      if (cancelled) return;
      setConformer(conf);
      setDescriptors(desc);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [smiles]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6 text-sm text-muted-foreground">
        Loading molecule data...
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 p-4 md:grid-cols-3">
      <div className="flex flex-col items-center gap-2">
        <MolViewer2D smiles={smiles} width={250} height={180} />
        <span className="font-mono text-xs text-muted-foreground">{name || smiles}</span>
      </div>

      {conformer && (
        <div className="flex flex-col items-center gap-2">
          <MolViewer3D molBlock={conformer.mol_block} width={250} height={180} />
          <span className="font-mono text-[11px] text-muted-foreground">
            Energy: {conformer.energy.toFixed(2)} kcal/mol ({conformer.num_atoms} atoms)
          </span>
        </div>
      )}

      {descriptors && (
        <div className="space-y-2 rounded-lg border border-border bg-surface p-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Properties</span>
            <span
              className={`rounded-full px-2 py-0.5 font-mono text-[11px] font-medium ${
                descriptors.passes_lipinski
                  ? "bg-primary/20 text-primary"
                  : "bg-destructive/20 text-destructive"
              }`}
            >
              {descriptors.passes_lipinski ? "Lipinski OK" : "Lipinski Fail"}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <Property label="MW" value={descriptors.molecular_weight.toFixed(1)} />
            <Property label="LogP" value={descriptors.logp.toFixed(2)} />
            <Property label="TPSA" value={descriptors.tpsa.toFixed(1)} />
            <Property label="HBD" value={String(descriptors.hbd)} />
            <Property label="HBA" value={String(descriptors.hba)} />
            <Property label="Rot. Bonds" value={String(descriptors.rotatable_bonds)} />
            <Property label="QED" value={descriptors.qed.toFixed(3)} />
            <Property label="Rings" value={String(descriptors.num_rings)} />
          </div>
        </div>
      )}
    </div>
  );
}

function Property({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

interface DockingViewerProps {
  proteinPdb: string;
  ligandMolBlock: string;
  width?: number;
  height?: number;
}

export function DockingViewer({
  proteinPdb,
  ligandMolBlock,
  width = 500,
  height = 400,
}: DockingViewerProps) {
  // TODO: Integrate 3Dmol.js for protein + ligand view
  return (
    <div
      className="flex items-center justify-center rounded-lg border border-border bg-white"
      style={{ width, height }}
    >
      <span className="text-xs text-muted-foreground">
        Docking viewer (protein: {proteinPdb.length}, ligand: {ligandMolBlock.length})
      </span>
    </div>
  );
}

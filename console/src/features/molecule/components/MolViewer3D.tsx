interface MolViewer3DProps {
  molBlock: string;
  width?: number;
  height?: number;
}

export function MolViewer3D({ molBlock, width = 400, height = 300 }: MolViewer3DProps) {
  // TODO: Integrate 3Dmol.js WebGL viewer
  return (
    <div
      className="flex items-center justify-center rounded-lg border border-border bg-white"
      style={{ width, height }}
    >
      <span className="text-xs text-muted-foreground">
        3D viewer ({molBlock.length} chars)
      </span>
    </div>
  );
}

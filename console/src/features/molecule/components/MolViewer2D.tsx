interface MolViewer2DProps {
  smiles: string;
  width?: number;
  height?: number;
}

export function MolViewer2D({ smiles, width = 300, height = 200 }: MolViewer2DProps) {
  // TODO: Integrate RDKit.js WASM for SVG rendering
  return (
    <div
      className="flex items-center justify-center rounded-lg border border-border bg-white"
      style={{ width, height }}
    >
      <span className="font-mono text-xs text-muted-foreground">{smiles}</span>
    </div>
  );
}

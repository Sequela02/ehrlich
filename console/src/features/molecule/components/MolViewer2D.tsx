import { useState } from "react";

interface MolViewer2DProps {
  smiles: string;
  width?: number;
  height?: number;
  className?: string;
}

export function MolViewer2D({ smiles, width = 300, height = 200, className }: MolViewer2DProps) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div
        className={`flex items-center justify-center rounded-lg border border-border bg-white ${className ?? ""}`}
        style={{ width, height }}
      >
        <span className="font-mono text-xs text-muted-foreground">{smiles}</span>
      </div>
    );
  }

  return (
    <img
      src={`/api/v1/molecule/depict?smiles=${encodeURIComponent(smiles)}&w=${width}&h=${height}`}
      alt={smiles}
      width={width}
      height={height}
      loading="lazy"
      className={`rounded-lg border border-border ${className ?? ""}`}
      onError={() => setError(true)}
    />
  );
}

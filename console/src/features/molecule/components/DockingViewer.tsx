import { useEffect, useRef } from "react";
import type { GLViewer } from "3dmol";

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
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<GLViewer | null>(null);

  useEffect(() => {
    if (!containerRef.current || !proteinPdb || !ligandMolBlock) return;

    let cancelled = false;

    import("3dmol").then(($3Dmol) => {
      if (cancelled || !containerRef.current) return;

      const viewer = $3Dmol.createViewer(containerRef.current, {
        backgroundColor: "white",
      });
      viewerRef.current = viewer;

      viewer.addModel(proteinPdb, "pdb");
      viewer.setStyle({ model: 0 }, { cartoon: { color: "spectrum" } });

      viewer.addModel(ligandMolBlock, "mol");
      viewer.setStyle({ model: 1 }, { stick: { colorscheme: "greenCarbon" } });

      viewer.zoomTo({ model: 1 });
      viewer.render();
    });

    return () => {
      cancelled = true;
      if (viewerRef.current) {
        viewerRef.current.clear();
        viewerRef.current = null;
      }
    };
  }, [proteinPdb, ligandMolBlock]);

  return (
    <div
      ref={containerRef}
      style={{ width, height, position: "relative" }}
      className="rounded-lg border border-border"
    />
  );
}

import { useEffect, useRef } from "react";
import type { GLViewer } from "3dmol";

interface MolViewer3DProps {
  molBlock: string;
  width?: number;
  height?: number;
}

export function MolViewer3D({ molBlock, width = 400, height = 300 }: MolViewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<GLViewer | null>(null);

  useEffect(() => {
    if (!containerRef.current || !molBlock) return;

    let cancelled = false;

    import("3dmol").then(($3Dmol) => {
      if (cancelled || !containerRef.current) return;

      const viewer = $3Dmol.createViewer(containerRef.current, {
        backgroundColor: "#1a1e1a",
      });
      viewerRef.current = viewer;
      viewer.addModel(molBlock, "sdf");
      viewer.setStyle({}, { stick: { colorscheme: "Jmol" } });
      viewer.zoomTo();
      viewer.render();
    });

    return () => {
      cancelled = true;
      if (viewerRef.current) {
        viewerRef.current.clear();
        viewerRef.current = null;
      }
    };
  }, [molBlock]);

  return (
    <div
      ref={containerRef}
      style={{ width, height, position: "relative" }}
      className="rounded-md border border-border"
    />
  );
}

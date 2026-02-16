import { useEffect, useRef } from "react";

interface MolViewer3DProps {
  molBlock: string;
  width?: number;
  height?: number;
  backgroundColor?: string;
}

export function MolViewer3D({ molBlock, width = 300, height = 300, backgroundColor = "#1a1e1a" }: MolViewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null); // Cast to any to avoid 3dmol type issues

  useEffect(() => {
    let cancelled = false;

    if (!containerRef.current || !molBlock) return;

    import("3dmol").then((mod) => {
      if (cancelled || !containerRef.current) return;

      try {
        const $3Dmol = mod.default || mod;

        // Ensure container has dimensions
        if (!containerRef.current.clientWidth || !containerRef.current.clientHeight) {
          // console.warn("MolViewer3D: Container has 0 dimensions", containerRef.current);
        }

        const config: any = { backgroundColor: backgroundColor };
        if (backgroundColor === "transparent") {
          // 3dmol requires alpha: 0 for transparency
          config.backgroundColor = "white";
          config.alpha = 0;
        }

        const viewer = $3Dmol.createViewer(containerRef.current, config);

        viewerRef.current = viewer;
        viewer.addModel(molBlock, "sdf");
        viewer.setStyle({}, { stick: { colorscheme: "Jmol" } });
        viewer.zoomTo();
        viewer.render();
        (viewer as any).spin("y", 0.15); // Add slow spin for effect
      } catch (e) {
        console.error("MolViewer3D Error:", e);
      }
    }).catch(err => console.error("Failed to load 3dmol", err));

    return () => {
      cancelled = true;
      if (viewerRef.current) {
        // viewerRef.current.clear(); // 3dmol might not have clear(), check docs. 
        // clear() usually clears models.
        (viewerRef.current as any).clear();
        viewerRef.current = null;
      }
    };
  }, [molBlock, backgroundColor]);

  return (
    <div
      ref={containerRef}
      style={{ width, height, position: "relative" }}
      className="rounded-md overflow-hidden relative" // Removed border to blend better? No, let's allow caller to style.
    />
  );
}

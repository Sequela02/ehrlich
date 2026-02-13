import { useEffect, useRef } from "react";
import { useReducedMotion } from "motion/react";

/**
 * Animated ASCII art background using textmode.js.
 * Renders a rotating 3D scientific structure (Icosahedron) to an offscreen canvas,
 * then converts it to ASCII in real-time.
 */
export function AsciiBackground({ className = "" }: { className?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced || !containerRef.current || !canvasRef.current) return;

    let disposed = false;
    let animationFrameId: number;
    let tmInstance: any = null;

    // 1. Setup offscreen canvas for 3D rendering
    const sourceCanvas = document.createElement("canvas");
    sourceCanvas.width = 160; // Low res for ASCII
    sourceCanvas.height = 90;
    const ctx = sourceCanvas.getContext("2d", { alpha: false });

    // 2. 3D Shape Logic (Icosahedron vertices)
    const t = (1 + Math.sqrt(5)) / 2;
    const vertices = [
      [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
      [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
      [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
    ];

    // Connections between vertices to form edges
    const edges = [
      [0, 11], [0, 5], [0, 1], [0, 7], [0, 10], [1, 5],
      [1, 7], [1, 8], [1, 9], [2, 11], [2, 4], [2, 10],
      [2, 6], [2, 3], [3, 4], [3, 9], [3, 8], [3, 6],
      [4, 5], [4, 9], [4, 11], [5, 11], [5, 1], [5, 4],
      [6, 7], [6, 10], [6, 3], [6, 2], [7, 8], [7, 6],
      [7, 1], [7, 0], [8, 9], [8, 3], [8, 1], [8, 7],
      [9, 4], [9, 3], [9, 8], [9, 1], [9, 5], [10, 11],
      [10, 2], [10, 6], [10, 7], [10, 0], [11, 4], [11, 2],
      [11, 10], [11, 5], [11, 0]
    ];

    let angleX = 0;
    let angleY = 0;

    const render3D = () => {
      if (!ctx) return;

      // Clear background (black)
      ctx.fillStyle = "#000000";
      ctx.fillRect(0, 0, sourceCanvas.width, sourceCanvas.height);

      // Drawing config
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.lineCap = "round";

      const cx = sourceCanvas.width / 2;
      const cy = sourceCanvas.height / 2;
      const scale = 30;

      // Rotation matrices
      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);
      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);

      const project = (v: number[]) => {
        let x = v[0], y = v[1], z = v[2];

        // Rotate Y
        let x1 = x * cosY - z * sinY;
        let z1 = z * cosY + x * sinY;

        // Rotate X
        let y1 = y * cosX - z1 * sinX;

        // Project 3D -> 2D
        return [
          cx + x1 * scale,
          cy + y1 * scale
        ];
      };

      ctx.beginPath();
      // Draw edges
      for (const [startIdx, endIdx] of edges) {
        const p1 = project(vertices[startIdx]);
        const p2 = project(vertices[endIdx]);

        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
      }
      ctx.stroke();

      angleX += 0.005;
      angleY += 0.008;
    };

    // 3. Initialize Textmode loop
    import("textmode.js").then(({ create }) => {
      if (disposed || !canvasRef.current) return;

      // @ts-expect-error textmode types are incomplete
      const tmPromise = create(canvasRef.current, {
        cols: 80,
        rows: 40,
        fg: "#72fbb9",
        bg: "#0d1117",
        font: "monospace"
      }) as Promise<any>;
      tmPromise.then((tm: any) => {
        tmInstance = tm;

        const loop = () => {
          if (disposed) return;

          render3D();

          // Feed the 3D canvas to textmode
          // @ts-ignore - textmode types might be loose or missing
          tm.renderFrom(sourceCanvas);

          animationFrameId = requestAnimationFrame(loop);
        };

        loop();
      });

    }).catch((e) => {
      console.warn("Textmode init failed:", e);
    });

    return () => {
      disposed = true;
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (tmInstance && tmInstance.destroy) tmInstance.destroy();
    };
  }, [reduced]);

  if (reduced) return null;

  return (
    <div ref={containerRef} className={`overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full object-cover opacity-20 mix-blend-screen"
      />
    </div>
  );
}

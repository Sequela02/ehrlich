import { useEffect, useRef } from "react";
import { useReducedMotion } from "motion/react";

/**
 * Animated ASCII art background using textmode.js (WebGL2 canvas).
 *
 * textmode.js is installed and ready. Once ASCII art assets are provided,
 * configure the renderer here. The library supports:
 * - Image/video to ASCII conversion (brightness + edge detection)
 * - Multi-layer rendering with blend modes
 * - Built-in filters (blur, sharpen, color adjustments)
 * - Plugin system for custom effects
 *
 * Docs: https://code.textmode.art/docs/introduction
 *
 * Usage:
 *   <AsciiBackground className="absolute inset-0 -z-10" />
 */
export function AsciiBackground({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || reduced) return;

    let disposed = false;

    // Dynamic import avoids SSR issues (textmode.js needs DOM + WebGL2)
    import("textmode.js").then(({ create }) => {
      if (disposed || !canvas) return;

      try {
        // `create` is the factory function: Textmode.create(canvas, options)
        // TODO: Configure with actual ASCII art assets
        // Example:
        //   const tm = await create(canvas, {
        //     font: { src: '/fonts/ascii.png', columns: 16, rows: 16 },
        //     grid: { columns: 80, rows: 40 },
        //   });
        //   tm.layers.create('background');
        //   // ... render ASCII art
        void create; // reference to suppress unused lint
      } catch {
        // WebGL2 not supported -- graceful fallback
      }
    }).catch(() => {
      // Module not available during SSR
    });

    return () => {
      disposed = true;
    };
  }, [reduced]);

  if (reduced) return null;

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
    />
  );
}

import { useEffect, useRef, useState } from "react";

/**
 * 3D molecular network rendered on Canvas 2D.
 * Nodes connected by proximity, rotating in 3D space.
 * Zero dependencies -- pure math + canvas API.
 *
 * SSR-safe: renders empty container on server, draws client-side only.
 * Reduced motion: renders a single static frame (no animation loop).
 */

const NODE_COUNT = 90;
const CONNECTION_DIST = 130;
const ROTATION_SPEED = 0.0003;
const FOV = 600;
const DEPTH = 300;
const MOUSE_REPEL_RADIUS = 200;
const MOUSE_REPEL_FORCE = 80;
const LERP_SPEED = 0.12;

// Ehrlich color palette
const PRIMARY = { r: 74, g: 222, b: 128 };    // #4ade80
const SECONDARY = { r: 13, g: 148, b: 136 };  // #0d9488
const ACCENT = { r: 234, g: 179, b: 8 };      // #eab308

interface Node3D {
  x: number;
  y: number;
  z: number;
  ox: number; // original position (for repulsion spring-back)
  oy: number;
  oz: number;
  radius: number;
  pulse: number;
  pulseSpeed: number;
}

function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return s / 2147483647;
  };
}

function createNodes(w: number, h: number): Node3D[] {
  const rand = seededRandom(42);
  const nodes: Node3D[] = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    const x = (rand() - 0.5) * w * 0.85;
    const y = (rand() - 0.5) * h * 0.85;
    const z = (rand() - 0.5) * DEPTH * 2;
    nodes.push({
      x, y, z, ox: x, oy: y, oz: z,
      radius: 1.5 + rand() * 2.5,
      pulse: rand() * Math.PI * 2,
      pulseSpeed: 0.015 + rand() * 0.02,
    });
  }
  return nodes;
}

function rotateY(x: number, z: number, angle: number): [number, number] {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return [x * cos - z * sin, x * sin + z * cos];
}

function rotateX(y: number, z: number, angle: number): [number, number] {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return [y * cos - z * sin, y * sin + z * cos];
}

function project(x: number, y: number, z: number, cx: number, cy: number) {
  const scale = FOV / (FOV + z + DEPTH);
  return {
    sx: x * scale + cx,
    sy: y * scale + cy,
    scale,
    depth: (z + DEPTH) / (DEPTH * 2),
  };
}

interface Projected {
  sx: number;
  sy: number;
  scale: number;
  depth: number;
  node: Node3D;
}

function drawFrame(
  ctx: CanvasRenderingContext2D,
  nodes: Node3D[],
  w: number,
  h: number,
  angleY: number,
  angleX: number,
  mouseX: number,
  mouseY: number,
  time: number,
) {
  ctx.clearRect(0, 0, w, h);

  const cx = w / 2;
  const cy = h / 2;

  const projected: Projected[] = nodes.map((node) => {
    const [rx, rz] = rotateY(node.x, node.z, angleY);
    const [ry, rz2] = rotateX(node.y, rz, angleX);
    return { ...project(rx, ry, rz2, cx, cy), node };
  });

  projected.sort((a, b) => b.depth - a.depth);

  // Draw connections with shimmer
  for (let i = 0; i < projected.length; i++) {
    for (let j = i + 1; j < projected.length; j++) {
      const a = projected[i];
      const b = projected[j];
      const dx = a.sx - b.sx;
      const dy = a.sy - b.sy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < CONNECTION_DIST) {
        const baseFade = (1 - dist / CONNECTION_DIST);
        const depthFade = 1 - (a.depth + b.depth) / 2;
        // Shimmer: subtle sine wave based on time + node indices
        const shimmer = 0.85 + 0.15 * Math.sin(time * 2 + i * 0.3 + j * 0.2);
        const opacity = baseFade * depthFade * 0.35 * shimmer;
        if (opacity < 0.01) continue;

        const midX = (a.sx + b.sx) / 2;
        const midY = (a.sy + b.sy) / 2;
        const mouseDist = Math.sqrt((midX - mouseX) ** 2 + (midY - mouseY) ** 2);
        const mouseBoost = mouseDist < 220 ? (1 - mouseDist / 220) * 0.8 : 0;

        // Near cursor: use primary green instead of teal
        const lineColor = mouseBoost > 0.15 ? PRIMARY : SECONDARY;

        ctx.beginPath();
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.strokeStyle = `rgba(${lineColor.r}, ${lineColor.g}, ${lineColor.b}, ${opacity + mouseBoost})`;
        ctx.lineWidth = 0.5 + depthFade * 0.8 + mouseBoost * 1.5;
        ctx.stroke();
      }
    }
  }

  // Draw nodes
  for (const p of projected) {
    const baseOpacity = (1 - p.depth) * 0.85 + 0.1;
    const pulseScale = 1 + Math.sin(p.node.pulse) * 0.15;
    const r = p.node.radius * p.scale * pulseScale;

    const mouseDist = Math.sqrt((p.sx - mouseX) ** 2 + (p.sy - mouseY) ** 2);
    const mouseGlow = mouseDist < 200 ? (1 - mouseDist / 200) : 0;

    const color = p.depth < 0.35 ? PRIMARY : p.depth < 0.65 ? SECONDARY : ACCENT;

    // Glow (always for visible nodes, much stronger near cursor)
    const glowRadius = r * (4 + mouseGlow * 10);
    const glowAlpha = baseOpacity * 0.25 + mouseGlow * 0.6;
    if (glowAlpha > 0.02) {
      const glow = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, glowRadius);
      glow.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${glowAlpha})`);
      glow.addColorStop(0.5, `rgba(${color.r}, ${color.g}, ${color.b}, ${glowAlpha * 0.3})`);
      glow.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, 0)`);
      ctx.beginPath();
      ctx.arc(p.sx, p.sy, glowRadius, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();
    }

    // Core dot
    ctx.beginPath();
    ctx.arc(p.sx, p.sy, r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${Math.min(1, baseOpacity + mouseGlow * 0.4)})`;
    ctx.fill();
  }

}

export function MolecularNetwork({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let w = 0;
    let h = 0;
    let nodes: Node3D[] = [];
    let angleY = 0;
    let angleX = 0.15;
    let frameId: number;
    let rawMouseX = -1000;
    let rawMouseY = -1000;
    let mouseX = -1000;
    let mouseY = -1000;
    let time = 0;

    function resize() {
      const rect = canvas!.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio, 2);
      w = rect.width;
      h = rect.height;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      nodes = createNodes(w, h);

      if (prefersReduced) {
        drawFrame(ctx!, nodes, w, h, angleY, angleX, mouseX, mouseY, 0);
      }
    }

    function handleMouse(e: PointerEvent) {
      const rect = canvas!.getBoundingClientRect();
      rawMouseX = e.clientX - rect.left;
      rawMouseY = e.clientY - rect.top;
    }

    function handleMouseLeave() {
      rawMouseX = -1000;
      rawMouseY = -1000;
    }

    resize();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", handleMouse);
    canvas.addEventListener("pointerleave", handleMouseLeave);

    // ResizeObserver catches parent layout/animation changes
    const ro = new ResizeObserver(() => resize());
    ro.observe(canvas);

    if (!prefersReduced) {
      function animate() {
        time += 0.016;
        angleY += ROTATION_SPEED;
        angleX += ROTATION_SPEED * 0.3;

        // Lerp mouse for smooth tracking
        mouseX += (rawMouseX - mouseX) * LERP_SPEED;
        mouseY += (rawMouseY - mouseY) * LERP_SPEED;

        // Cursor repulsion + spring-back
        const cx = w / 2;
        const cy = h / 2;
        for (const node of nodes) {
          node.pulse += node.pulseSpeed;

          // Project to get screen position for mouse interaction
          const [rx, rz] = rotateY(node.x, node.z, angleY);
          const [ry, rz2] = rotateX(node.y, rz, angleX);
          const p = project(rx, ry, rz2, cx, cy);
          const dx = p.sx - mouseX;
          const dy = p.sy - mouseY;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < MOUSE_REPEL_RADIUS && dist > 0) {
            const force = (1 - dist / MOUSE_REPEL_RADIUS) * MOUSE_REPEL_FORCE;
            node.x += (dx / dist) * force * 0.15;
            node.y += (dy / dist) * force * 0.15;
          }

          // Spring back to original position (slow enough to see the push)
          node.x += (node.ox - node.x) * 0.01;
          node.y += (node.oy - node.y) * 0.01;
          node.z += (node.oz - node.z) * 0.01;
        }

        drawFrame(ctx!, nodes, w, h, angleY, angleX, mouseX, mouseY, time);
        frameId = requestAnimationFrame(animate);
      }
      frameId = requestAnimationFrame(animate);
    }

    return () => {
      if (frameId) cancelAnimationFrame(frameId);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", handleMouse);
      canvas.removeEventListener("pointerleave", handleMouseLeave);
      ro.disconnect();
    };
  }, [mounted]);

  return (
    <canvas
      ref={canvasRef}
      className={`w-full h-full pointer-events-auto ${className}`}
      style={{
        touchAction: "none",
        maskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 100%)",
        WebkitMaskImage: "radial-gradient(ellipse 70% 70% at center, black 40%, transparent 100%)",
      }}
      aria-hidden="true"
    />
  );
}

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";

/**
 * Rotating 3D torus rendered as ASCII characters.
 * Based on the classic "donut.c" algorithm by Andy Sloane.
 * https://www.a1k0n.net/2011/07/20/donut-math.html
 */

const CHARS = ".,-~:;=!*#$@";
const COLS = 50;
const ROWS = 25;

// Torus parameters
const R1 = 1; // tube radius
const R2 = 2; // ring radius
const K2 = 5; // distance from viewer
const K1 = COLS * K2 * 3 / (8 * (R1 + R2));

function renderFrame(A: number, B: number): string {
  const output: string[] = new Array(COLS * ROWS).fill(" ");
  const zbuffer: number[] = new Array(COLS * ROWS).fill(0);

  const cosA = Math.cos(A), sinA = Math.sin(A);
  const cosB = Math.cos(B), sinB = Math.sin(B);

  for (let theta = 0; theta < 6.28; theta += 0.07) {
    const cosTheta = Math.cos(theta), sinTheta = Math.sin(theta);

    for (let phi = 0; phi < 6.28; phi += 0.02) {
      const cosPhi = Math.cos(phi), sinPhi = Math.sin(phi);

      const circleX = R2 + R1 * cosTheta;
      const circleY = R1 * sinTheta;

      const x = circleX * (cosB * cosPhi + sinA * sinB * sinPhi) - circleY * cosA * sinB;
      const y = circleX * (sinB * cosPhi - sinA * cosB * sinPhi) + circleY * cosA * cosB;
      const z = K2 + cosA * circleX * sinPhi + circleY * sinA;
      const ooz = 1 / z;

      const xp = Math.floor(COLS / 2 + K1 * ooz * x);
      const yp = Math.floor(ROWS / 2 - K1 * ooz * y * 0.5);

      if (xp < 0 || xp >= COLS || yp < 0 || yp >= ROWS) continue;

      const idx = xp + yp * COLS;

      const L = cosPhi * cosTheta * sinB
        - cosA * cosTheta * sinPhi
        - sinA * sinTheta
        + cosB * (cosA * sinTheta - cosTheta * sinA * sinPhi);

      if (ooz > zbuffer[idx]) {
        zbuffer[idx] = ooz;
        const luminanceIdx = Math.max(0, Math.floor(L * 8));
        output[idx] = CHARS[Math.min(luminanceIdx, CHARS.length - 1)];
      }
    }
  }

  let text = "";
  for (let j = 0; j < ROWS; j++) {
    for (let i = 0; i < COLS; i++) {
      text += output[i + j * COLS];
    }
    text += "\n";
  }
  return text;
}

// Pre-compute a static frame for SSR / initial render
const STATIC_FRAME = renderFrame(0.8, 0.6);

export function AsciiTorus({ className = "" }: { className?: string }) {
  const preRef = useRef<HTMLPreElement>(null);
  const reduced = useReducedMotion();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (reduced || !mounted || !preRef.current) return;

    let A = 0.8;
    let B = 0.6;
    let frameId: number;

    const animate = () => {
      A += 0.04;
      B += 0.02;
      if (preRef.current) {
        preRef.current.textContent = renderFrame(A, B);
      }
      frameId = requestAnimationFrame(animate);
    };

    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [reduced, mounted]);

  if (reduced) {
    return null;
  }

  return (
    <pre
      ref={preRef}
      className={`font-mono text-[13px] leading-[1.15] text-primary select-none ${className}`}
      style={{ textShadow: "0 0 8px oklch(0.72 0.19 155 / 0.4)" }}
      aria-hidden="true"
    >
      {STATIC_FRAME}
    </pre>
  );
}

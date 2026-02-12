interface ColorStop {
  position: number;
  l: number;
  c: number;
  h: number;
}

const ACTIVATION_STOPS: ColorStop[] = [
  { position: 0.0, l: 0.45, c: 0.05, h: 250 },
  { position: 0.3, l: 0.55, c: 0.12, h: 160 },
  { position: 0.6, l: 0.65, c: 0.18, h: 85 },
  { position: 1.0, l: 0.63, c: 0.22, h: 25 },
];

const RISK_STOPS: ColorStop[] = [
  { position: 0.0, l: 0.55, c: 0.12, h: 160 },
  { position: 0.5, l: 0.65, c: 0.18, h: 85 },
  { position: 1.0, l: 0.55, c: 0.22, h: 25 },
];

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpHue(a: number, b: number, t: number): number {
  let diff = b - a;
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;
  const result = a + diff * t;
  return ((result % 360) + 360) % 360;
}

function interpolateStops(intensity: number, stops: ColorStop[]): string {
  const clamped = Math.max(0, Math.min(1, intensity));

  for (let i = 0; i < stops.length - 1; i++) {
    const curr = stops[i];
    const next = stops[i + 1];
    if (clamped >= curr.position && clamped <= next.position) {
      const t = (clamped - curr.position) / (next.position - curr.position);
      const l = lerp(curr.l, next.l, t);
      const c = lerp(curr.c, next.c, t);
      const h = lerpHue(curr.h, next.h, t);
      return `oklch(${l.toFixed(3)} ${c.toFixed(3)} ${h.toFixed(1)})`;
    }
  }

  const last = stops[stops.length - 1];
  return `oklch(${last.l.toFixed(3)} ${last.c.toFixed(3)} ${last.h.toFixed(1)})`;
}

export function getIntensityColor(
  intensity: number,
  mode: 'activation' | 'risk',
): string {
  return interpolateStops(
    intensity,
    mode === 'activation' ? ACTIVATION_STOPS : RISK_STOPS,
  );
}

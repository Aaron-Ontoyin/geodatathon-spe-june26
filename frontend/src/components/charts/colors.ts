// Shared chart palette, mirroring tokens.css for canvas/SVG drawing.
// The ramp runs cream -> sand -> amber -> clay -> rust: low resource recedes
// into the warm canvas, hotspots deepen so they read on a light background.

export const ACCENT = {
  heat: "#c2603f",
  heatHi: "#9e4527",
  cool: "#2f8f89",
  coolHi: "#1f6f6a",
  grid: "rgba(58,50,38,0.10)",
  axis: "rgba(58,50,38,0.32)",
  text: "#645d4e",
  bad: "#be4636",
};

// Warm sequential control points (cream -> rust), sampled by lerp.
const RAMP: [number, number, number][] = [
  [240, 237, 227], // cream (low — blends into the canvas)
  [233, 211, 170], // pale sand
  [223, 169, 102], // amber
  [203, 120, 70], // clay
  [165, 74, 44], // deep clay
  [120, 46, 28], // rust (high)
];

/** Map t in [0,1] to an rgb() string on the warm cream->rust ramp. */
export function magma(t: number): string {
  const x = Math.min(Math.max(t, 0), 1) * (RAMP.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = RAMP[i];
  const b = RAMP[Math.min(i + 1, RAMP.length - 1)];
  const c = (k: number) => Math.round(a[k] + (b[k] - a[k]) * f);
  return `rgb(${c(0)}, ${c(1)}, ${c(2)})`;
}

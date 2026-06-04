// Shared chart palette, mirroring tokens.css for canvas/SVG drawing.
// The ramp is a cartographic hypsometric tint: pale stone -> teal -> indigo,
// so low resource recedes into the vellum and hotspots read as deep "elevation".

export const ACCENT = {
  heat: "#b06640", // burnt sienna, heating series / viable wells
  heatHi: "#8c4626",
  cool: "#2b6e7a", // deep teal, primary / cooling series
  coolHi: "#1c545f",
  grid: "rgba(38,52,52,0.10)",
  axis: "rgba(38,52,52,0.32)",
  text: "#5a6765",
  bad: "#bb4a3a",
};

// Cartographic elevation control points (stone -> teal -> indigo), sampled by lerp.
const RAMP: [number, number, number][] = [
  [232, 236, 226], // pale stone (low, blends into the canvas)
  [185, 207, 198], // sage stone
  [111, 163, 158], // shallow teal
  [43, 110, 122], // deep teal
  [42, 79, 122], // indigo (high)
];

/** Map t in [0,1] to an rgb() string on the cartographic stone->indigo ramp. */
export function magma(t: number): string {
  const x = Math.min(Math.max(t, 0), 1) * (RAMP.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = RAMP[i];
  const b = RAMP[Math.min(i + 1, RAMP.length - 1)];
  const c = (k: number) => Math.round(a[k] + (b[k] - a[k]) * f);
  return `rgb(${c(0)}, ${c(1)}, ${c(2)})`;
}

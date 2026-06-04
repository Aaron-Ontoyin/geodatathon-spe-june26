// Shared chart palette. The magma ramp evokes molten subsurface heat.

export const ACCENT = {
  heat: "#ff8a3d",
  heatHi: "#ffb066",
  cool: "#45d0c0",
  coolHi: "#74e6d8",
  grid: "rgba(150,175,210,0.12)",
  axis: "rgba(150,175,210,0.45)",
  text: "#8a99ad",
  bad: "#ff5d5d",
};

// Magma-like control points (dark -> molten -> pale), sampled by lerp.
const MAGMA: [number, number, number][] = [
  [10, 8, 30],
  [60, 15, 80],
  [125, 30, 95],
  [190, 50, 80],
  [240, 95, 60],
  [253, 160, 70],
  [254, 220, 130],
];

/** Map t in [0,1] to a magma rgb() string. */
export function magma(t: number): string {
  const x = Math.min(Math.max(t, 0), 1) * (MAGMA.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = MAGMA[i];
  const b = MAGMA[Math.min(i + 1, MAGMA.length - 1)];
  const c = (k: number) => Math.round(a[k] + (b[k] - a[k]) * f);
  return `rgb(${c(0)}, ${c(1)}, ${c(2)})`;
}

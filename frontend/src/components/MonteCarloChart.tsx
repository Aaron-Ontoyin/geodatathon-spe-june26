import { Panel } from "./Panel";
import { ACCENT, magma } from "./charts/colors";
import type { MonteCarlo } from "../api/types";

interface MonteCarloChartProps {
  mc: MonteCarlo;
}

// Geometry of the plotting surface (viewBox units; rendered at width:100%).
const VB_W = 560;
const VB_H = 280;
const PAD = { top: 26, right: 14, bottom: 34, left: 40 };
const PLOT_W = VB_W - PAD.left - PAD.right;
const PLOT_H = VB_H - PAD.top - PAD.bottom;

interface RefLine {
  value: number;
  name: string;
  color: string;
}

/** LCoE Monte-Carlo histogram with P10/P50/P90 reference lines. */
export function MonteCarloChart({ mc }: MonteCarloChartProps) {
  const { hist_counts, hist_edges, p10, p50, p90, mean } = mc;
  const n = hist_counts.length;

  // Bin centres from edges (length = counts + 1).
  const centres: number[] = [];
  for (let i = 0; i < n; i++) {
    const lo = hist_edges[i] ?? 0;
    const hi = hist_edges[i + 1] ?? lo;
    centres.push((lo + hi) / 2);
  }

  // X domain: clip to [0, p90 * 1.4] so the long molten tail stays readable.
  const xMin = 0;
  const xMax = Math.max(p90 * 1.4, hist_edges[1] ?? 1, 1e-6);
  const maxCount = Math.max(1, ...hist_counts);

  const xScale = (v: number) => PAD.left + ((v - xMin) / (xMax - xMin)) * PLOT_W;
  const yScale = (c: number) => PAD.top + PLOT_H - (c / maxCount) * PLOT_H;

  // X ticks: a handful of evenly spaced €/GJ marks.
  const TICKS = 5;
  const xTicks: number[] = [];
  for (let i = 0; i <= TICKS; i++) xTicks.push(xMin + ((xMax - xMin) * i) / TICKS);

  // Colour each bar by its position across the full distribution span (magma).
  const cMin = centres.length ? Math.min(...centres) : 0;
  const cMax = centres.length ? Math.max(...centres) : 1;
  const cSpan = cMax - cMin || 1;

  const refs: RefLine[] = [
    { value: p10, name: "P10", color: "var(--good)" },
    { value: p50, name: "P50", color: "var(--text)" },
    { value: p90, name: "P90", color: "var(--bad)" },
  ];

  const axisStyle = {
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    fill: ACCENT.text,
  } as const;

  return (
    <Panel
      label="LCoE UNCERTAINTY (MONTE-CARLO)"
      accent="heat"
      right={
        <span className="mono num" style={{ color: "var(--text-dim)", fontSize: 11 }}>
          μ {mean.toFixed(1)} €/GJ
        </span>
      }
    >
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        width="100%"
        height={VB_H}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="LCoE Monte-Carlo distribution histogram"
      >
        {/* Horizontal gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((g) => {
          const y = PAD.top + PLOT_H - g * PLOT_H;
          return (
            <line
              key={`g${g}`}
              x1={PAD.left}
              x2={PAD.left + PLOT_W}
              y1={y}
              y2={y}
              stroke={ACCENT.grid}
              strokeWidth={1}
            />
          );
        })}

        {/* Histogram bars, magma-graded across the distribution */}
        {hist_counts.map((count, i) => {
          const c = centres[i];
          if (c == null || c > xMax || count <= 0) return null;
          const lo = hist_edges[i] ?? c;
          const hi = hist_edges[i + 1] ?? c;
          const x0 = xScale(Math.max(lo, xMin));
          const x1 = xScale(Math.min(hi, xMax));
          const w = Math.max(0.5, x1 - x0 - 0.6);
          const y = yScale(count);
          const h = PAD.top + PLOT_H - y;
          const t = (c - cMin) / cSpan;
          return (
            <rect
              key={`b${i}`}
              x={x0}
              y={y}
              width={w}
              height={Math.max(0, h)}
              fill={magma(t)}
              opacity={0.92}
            />
          );
        })}

        {/* X axis baseline */}
        <line
          x1={PAD.left}
          x2={PAD.left + PLOT_W}
          y1={PAD.top + PLOT_H}
          y2={PAD.top + PLOT_H}
          stroke={ACCENT.axis}
          strokeWidth={1}
        />

        {/* X ticks + labels */}
        {xTicks.map((tk, i) => {
          const x = xScale(tk);
          return (
            <g key={`xt${i}`}>
              <line
                x1={x}
                x2={x}
                y1={PAD.top + PLOT_H}
                y2={PAD.top + PLOT_H + 4}
                stroke={ACCENT.axis}
                strokeWidth={1}
              />
              <text
                x={x}
                y={PAD.top + PLOT_H + 16}
                textAnchor="middle"
                style={axisStyle}
              >
                {tk.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* X axis unit */}
        <text
          x={PAD.left + PLOT_W}
          y={VB_H - 4}
          textAnchor="end"
          style={{ ...axisStyle, fill: ACCENT.text }}
        >
          €/GJ
        </text>

        {/* Reference lines: P10 / P50 / P90 */}
        {refs.map((r) => {
          if (r.value > xMax) return null;
          const x = xScale(r.value);
          return (
            <g key={r.name}>
              <line
                x1={x}
                x2={x}
                y1={PAD.top - 4}
                y2={PAD.top + PLOT_H}
                stroke={r.color}
                strokeWidth={1}
                strokeDasharray="3 3"
              />
              <text
                x={x}
                y={PAD.top - 14}
                textAnchor="middle"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  fill: r.color,
                  letterSpacing: "0.05em",
                }}
              >
                {r.name}
              </text>
              <text
                x={x}
                y={PAD.top - 4}
                textAnchor="middle"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  fill: r.color,
                }}
              >
                {r.value.toFixed(1)}
              </text>
            </g>
          );
        })}
      </svg>
    </Panel>
  );
}

import { Panel } from "./Panel";
import { ACCENT } from "./charts/colors";
import type { Percentile } from "../api/types";

interface PercentilesChartProps {
  data: Percentile[];
}

const ROW_H = 26; // px per well
const PAD_TOP = 14;
const PAD_BOTTOM = 30;
const PAD_LEFT = 64; // room for well id labels
const PAD_RIGHT = 18;
const VB_W = 600; // viewBox width; svg stretches to 100%
const BAR_H = 10;
const TARGET = 10; // MWth target line

/** "Nice" upper bound + a small set of round tick values for the x axis. */
function axisTicks(max: number): { bound: number; ticks: number[] } {
  const safe = max > 0 ? max : 1;
  const raw = safe / 4;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / pow;
  const step = (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * pow;
  const bound = Math.ceil(safe / step) * step;
  const ticks: number[] = [];
  for (let v = 0; v <= bound + 1e-9; v += step) ticks.push(Number(v.toFixed(6)));
  return { bound, ticks };
}

/** SVG per-well power bands: P90 -> P10 range with a bold P50 tick. */
export function PercentilesChart({ data }: PercentilesChartProps) {
  const plotW = VB_W - PAD_LEFT - PAD_RIGHT;
  const innerH = data.length * ROW_H;
  const vbH = PAD_TOP + innerH + PAD_BOTTOM;

  const maxP10 = data.reduce((m, d) => Math.max(m, d.p10), 0);
  const { bound, ticks } = axisTicks(Math.max(maxP10, TARGET));

  const xOf = (v: number) => PAD_LEFT + (v / bound) * plotW;
  const axisY = PAD_TOP + innerH;
  const targetX = xOf(TARGET);

  return (
    <Panel label="PER-WELL POWER  P90 · P50 · P10 (MWth)" accent="heat">
      <svg
        viewBox={`0 0 ${VB_W} ${vbH}`}
        width="100%"
        height={vbH}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Per-well power percentile bands"
        style={{ display: "block", fontFamily: "var(--font-mono)" }}
      >
        {/* vertical gridlines */}
        {ticks.map((t) => (
          <line
            key={`g-${t}`}
            x1={xOf(t)}
            x2={xOf(t)}
            y1={PAD_TOP}
            y2={axisY}
            stroke={ACCENT.grid}
            strokeWidth={1}
          />
        ))}

        {/* x axis */}
        <line
          x1={PAD_LEFT}
          x2={PAD_LEFT + plotW}
          y1={axisY}
          y2={axisY}
          stroke={ACCENT.axis}
          strokeWidth={1}
        />

        {/* x axis tick labels */}
        {ticks.map((t) => (
          <text
            key={`tl-${t}`}
            x={xOf(t)}
            y={axisY + 14}
            fill={ACCENT.text}
            fontSize={10}
            textAnchor="middle"
          >
            {t}
          </text>
        ))}

        {/* per-well range bars */}
        {data.map((d, i) => {
          const cy = PAD_TOP + i * ROW_H + ROW_H / 2;
          const x90 = xOf(d.p90);
          const x10 = xOf(d.p10);
          const x50 = xOf(d.p50);
          const barX = Math.min(x90, x10);
          const barW = Math.max(Math.abs(x10 - x90), 1);
          return (
            <g key={d.well}>
              {/* well id label */}
              <text
                x={PAD_LEFT - 10}
                y={cy + 3}
                fill="var(--text-dim)"
                fontSize={11}
                textAnchor="end"
              >
                {d.well}
              </text>

              {/* P90..P10 range */}
              <rect
                x={barX}
                y={cy - BAR_H / 2}
                width={barW}
                height={BAR_H}
                rx={BAR_H / 2}
                ry={BAR_H / 2}
                fill={ACCENT.heat}
                fillOpacity={0.18}
                stroke={ACCENT.heat}
                strokeOpacity={0.35}
                strokeWidth={1}
              />

              {/* P50 bold tick */}
              <line
                x1={x50}
                x2={x50}
                y1={cy - BAR_H / 2 - 2}
                y2={cy + BAR_H / 2 + 2}
                stroke={ACCENT.heatHi}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
            </g>
          );
        })}

        {/* target line: 10 MWth */}
        <line
          x1={targetX}
          x2={targetX}
          y1={PAD_TOP - 4}
          y2={axisY}
          stroke={ACCENT.cool}
          strokeWidth={1}
          strokeDasharray="4 3"
        />
        <text
          x={targetX + 4}
          y={PAD_TOP + 4}
          fill={ACCENT.cool}
          fontSize={10}
          textAnchor="start"
        >
          10 MWth target
        </text>
      </svg>
    </Panel>
  );
}

import { Panel } from "./Panel";
import { ACCENT } from "./charts/colors";
import type { TornadoRow } from "../api/types";

interface TornadoChartProps {
  rows: TornadoRow[];
}

const ROW_H = 26; // px per row
const PAD_TOP = 14;
const PAD_BOTTOM = 30;
const PAD_LEFT = 170; // room for prettified field names
const PAD_RIGHT = 78; // room for swing readout
const VB_W = 640; // viewBox width; svg stretches to 100%
const BAR_H = 12;
const NAME_MAX = 22;

/** Prettify a backend field name: underscores -> spaces, truncated. */
function prettify(field: string): string {
  const s = field.replace(/_/g, " ");
  return s.length > NAME_MAX ? `${s.slice(0, NAME_MAX - 1)}…` : s;
}

/** "Nice" round step for a span, used to derive symmetric axis ticks. */
function niceStep(span: number): number {
  const raw = (span > 0 ? span : 1) / 4;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / pow;
  return (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * pow;
}

/** SVG sensitivity tornado: low..high LCoE bars centred on a shared baseline. */
export function TornadoChart({ rows }: TornadoChartProps) {
  const plotW = VB_W - PAD_LEFT - PAD_RIGHT;
  const innerH = rows.length * ROW_H;
  const vbH = PAD_TOP + innerH + PAD_BOTTOM;

  // Shared x scale across rows: span the full min(low)..max(high) range.
  const lo = rows.reduce((m, r) => Math.min(m, r.low, r.high), Infinity);
  const hi = rows.reduce((m, r) => Math.max(m, r.low, r.high), -Infinity);
  const domLo = Number.isFinite(lo) ? lo : 0;
  const domHi = Number.isFinite(hi) ? hi : 1;
  // Baseline = midpoint of the overall range (the "neutral" LCoE).
  const baseline = (domLo + domHi) / 2;
  const half = Math.max(domHi - baseline, baseline - domLo, 1e-6);
  const min = baseline - half;
  const max = baseline + half;

  const xOf = (v: number) => PAD_LEFT + ((v - min) / (max - min)) * plotW;
  const axisY = PAD_TOP + innerH;
  const baseX = xOf(baseline);

  // Symmetric ticks around the baseline.
  const step = niceStep(half);
  const ticks: number[] = [];
  for (let v = baseline; v <= max + 1e-9; v += step) ticks.push(Number(v.toFixed(6)));
  for (let v = baseline - step; v >= min - 1e-9; v -= step) ticks.push(Number(v.toFixed(6)));

  return (
    <Panel label="WHAT MOVES THE LCoE (SENSITIVITY)" accent="heat">
      <svg
        viewBox={`0 0 ${VB_W} ${vbH}`}
        width="100%"
        height={vbH}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="LCoE sensitivity tornado"
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
            {t.toFixed(1)}
          </text>
        ))}

        {/* per-field bars: cheaper (left) in cool, pricier (right) in heat */}
        {rows.map((r) => {
          // index by position in incoming (sorted desc) order
          const i = rows.indexOf(r);
          const cy = PAD_TOP + i * ROW_H + ROW_H / 2;
          const xLow = xOf(r.low);
          const xHigh = xOf(r.high);
          const left = Math.min(xLow, xHigh);
          const right = Math.max(xLow, xHigh);
          // split the bar at the baseline into cool/heat halves
          const splitL = Math.min(left, baseX);
          const splitR = Math.max(right, baseX);
          const coolW = Math.max(baseX - left, 0);
          const heatW = Math.max(right - baseX, 0);
          const yTop = cy - BAR_H / 2;

          return (
            <g key={r.field}>
              {/* field name */}
              <text
                x={PAD_LEFT - 12}
                y={cy + 3}
                fill="var(--text-dim)"
                fontSize={11}
                textAnchor="end"
              >
                {prettify(r.field)}
              </text>

              {/* cheaper half */}
              {coolW > 0 && (
                <rect
                  x={splitL}
                  y={yTop}
                  width={coolW}
                  height={BAR_H}
                  fill="var(--cool)"
                  fillOpacity={0.78}
                />
              )}

              {/* pricier half */}
              {heatW > 0 && (
                <rect
                  x={baseX}
                  y={yTop}
                  width={Math.max(splitR - baseX, 0)}
                  height={BAR_H}
                  fill="var(--heat)"
                  fillOpacity={0.78}
                />
              )}

              {/* swing readout */}
              <text
                x={PAD_LEFT + plotW + 10}
                y={cy + 3}
                fill="var(--text)"
                fontSize={11}
                textAnchor="start"
              >
                {`±${(r.swing / 2).toFixed(1)}`}
              </text>
            </g>
          );
        })}

        {/* centre baseline axis (drawn last, on top of bars) */}
        <line
          x1={baseX}
          x2={baseX}
          y1={PAD_TOP - 4}
          y2={axisY}
          stroke={ACCENT.axis}
          strokeWidth={1}
        />
        <text
          x={baseX}
          y={PAD_TOP - 6}
          fill={ACCENT.text}
          fontSize={10}
          textAnchor="middle"
        >
          {baseline.toFixed(1)}
        </text>
      </svg>
    </Panel>
  );
}

import { Panel } from "./Panel";
import { ACCENT } from "./charts/colors";
import type { DesignSeries } from "../api/types";

interface DispatchChartProps {
  design: DesignSeries;
}

const MONTH_INITIALS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

// SVG geometry for the dispatch column chart (user-space coordinates).
const VIEW_W = 600;
const VIEW_H = 240;
const PAD_L = 40;
const PAD_R = 12;
const PAD_T = 14;
const PAD_B = 24;
const PLOT_W = VIEW_W - PAD_L - PAD_R;
const PLOT_H = VIEW_H - PAD_T - PAD_B;

/** Round a max value up to a clean axis tick. */
function niceMax(value: number): number {
  if (value <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(value)));
  const norm = value / pow;
  const step = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10;
  return step * pow;
}

/**
 * Monthly dispatch (heating + cooling columns over a geo-heat line) with a
 * capacity-factor uplift comparison. Hand-rolled SVG, instrument styling.
 */
export function DispatchChart({ design }: DispatchChartProps) {
  const { heating_mw, cooling_mw, geo_heat_mw } = design;
  const n = Math.max(heating_mw.length, 1);

  const peak = Math.max(
    1,
    ...heating_mw,
    ...cooling_mw,
    ...geo_heat_mw,
  );
  const yMax = niceMax(peak);

  const yToPx = (mw: number) => PAD_T + PLOT_H * (1 - mw / yMax);
  const slot = PLOT_W / n;
  const heatW = slot * 0.42;
  const coolW = slot * 0.22;
  const gap = slot * 0.06;
  const groupW = heatW + coolW + gap;

  // Horizontal gridlines + MW axis ticks (0, ¼, ½, ¾, full).
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);

  // Geo-heat overlay polyline through the centre of each month slot.
  const geoPoints = geo_heat_mw
    .map((mw, i) => `${(PAD_L + slot * (i + 0.5)).toFixed(1)},${yToPx(mw).toFixed(1)}`)
    .join(" ");

  const cfHeatOnly = design.capacity_factor_heating_only * 100;
  const cfWithCooling = design.capacity_factor * 100;
  const cfPctMax = Math.max(cfHeatOnly, cfWithCooling, 1);

  return (
    <Panel
      label="MONTHLY DISPATCH & UTILISATION"
      accent="cool"
      right={
        <span className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
          {design.heat_gwh.toFixed(0)} GWh<sub style={{ fontSize: 9 }}>th</sub> ·{" "}
          {design.cool_gwh.toFixed(0)} GWh<sub style={{ fontSize: 9 }}>c</sub>
        </span>
      }
    >
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        width="100%"
        height={240}
        style={{ display: "block" }}
        role="img"
        aria-label="Monthly heating and cooling dispatch in megawatts"
      >
        {/* Gridlines + y-axis labels (MW) */}
        {ticks.map((t, i) => {
          const y = yToPx(t);
          return (
            <g key={`grid-${i}`}>
              <line
                x1={PAD_L}
                x2={VIEW_W - PAD_R}
                y1={y}
                y2={y}
                stroke={ACCENT.grid}
                strokeWidth={1}
              />
              <text
                x={PAD_L - 6}
                y={y + 3}
                textAnchor="end"
                fontFamily="var(--font-mono)"
                fontSize={10}
                fill={ACCENT.text}
              >
                {t.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Y-axis title */}
        <text
          x={PAD_L - 30}
          y={PAD_T + PLOT_H / 2}
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize={10}
          fill={ACCENT.text}
          transform={`rotate(-90 ${PAD_L - 30} ${PAD_T + PLOT_H / 2})`}
        >
          MW
        </text>

        {/* Baseline axis */}
        <line
          x1={PAD_L}
          x2={VIEW_W - PAD_R}
          y1={yToPx(0)}
          y2={yToPx(0)}
          stroke={ACCENT.axis}
          strokeWidth={1}
        />

        {/* Columns: heating (heat) + thinner cooling (cool) per month */}
        {heating_mw.map((h, i) => {
          const base = yToPx(0);
          const groupLeft = PAD_L + slot * (i + 0.5) - groupW / 2;
          const hx = groupLeft;
          const cx = groupLeft + heatW + gap;
          const hY = yToPx(h);
          const cMw = cooling_mw[i] ?? 0;
          const cY = yToPx(cMw);
          return (
            <g key={`col-${i}`}>
              <rect
                x={hx}
                y={hY}
                width={heatW}
                height={Math.max(0, base - hY)}
                fill="var(--heat)"
                rx={1}
              />
              <rect
                x={cx}
                y={cY}
                width={coolW}
                height={Math.max(0, base - cY)}
                fill="var(--cool)"
                rx={1}
              />
              <text
                x={PAD_L + slot * (i + 0.5)}
                y={base + 15}
                textAnchor="middle"
                fontFamily="var(--font-mono)"
                fontSize={10}
                fill={ACCENT.text}
              >
                {MONTH_INITIALS[design.months[i] != null ? (design.months[i] - 1 + 12) % 12 : i]}
              </text>
            </g>
          );
        })}

        {/* Faint geo-heat capacity overlay line */}
        {geo_heat_mw.length > 1 && (
          <polyline
            points={geoPoints}
            fill="none"
            stroke={ACCENT.heatHi}
            strokeWidth={1.25}
            strokeOpacity={0.55}
            strokeDasharray="3 3"
          />
        )}
      </svg>

      {/* Legend */}
      <div
        style={{
          display: "flex",
          gap: 18,
          marginTop: 4,
          fontSize: 10,
          color: "var(--text-dim)",
        }}
        className="mono"
      >
        <LegendSwatch color="var(--heat)" labelText="HEATING" />
        <LegendSwatch color="var(--cool)" labelText="COOLING" />
        <LegendLine color={ACCENT.heatHi} labelText="GEO HEAT" />
      </div>

      {/* Capacity-factor uplift bars */}
      <div style={{ marginTop: 18, display: "flex", flexDirection: "column", gap: 12 }}>
        <span className="label" style={{ color: "var(--text-faint)" }}>
          CAPACITY FACTOR UPLIFT
        </span>
        <CfBar
          labelText="HEATING ONLY"
          pct={cfHeatOnly}
          maxPct={cfPctMax}
          fill="var(--heat)"
          valueColor="var(--text)"
        />
        <CfBar
          labelText="WITH COOLING"
          pct={cfWithCooling}
          maxPct={cfPctMax}
          fill="var(--cool)"
          valueColor="var(--cool-hi)"
        />
      </div>
    </Panel>
  );
}

interface LegendProps {
  color: string;
  labelText: string;
}

function LegendSwatch({ color, labelText }: LegendProps) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          width: 10,
          height: 10,
          background: color,
          borderRadius: 2,
          display: "inline-block",
        }}
      />
      {labelText}
    </span>
  );
}

function LegendLine({ color, labelText }: LegendProps) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          width: 14,
          height: 0,
          borderTop: `1.5px dashed ${color}`,
          opacity: 0.7,
          display: "inline-block",
        }}
      />
      {labelText}
    </span>
  );
}

interface CfBarProps {
  labelText: string;
  pct: number;
  maxPct: number;
  fill: string;
  valueColor: string;
}

function CfBar({ labelText, pct, maxPct, fill, valueColor }: CfBarProps) {
  const widthPct = `${((pct / maxPct) * 100).toFixed(1)}%`;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <span
        className="label"
        style={{ width: 96, flex: "0 0 auto", color: "var(--text-dim)" }}
      >
        {labelText}
      </span>
      <div
        style={{
          position: "relative",
          flex: 1,
          height: 8,
          background: "var(--bg-0)",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            width: widthPct,
            background: fill,
            borderRadius: 4,
            transition: "width 0.3s var(--ease)",
          }}
        />
      </div>
      <span
        className="mono num"
        style={{ width: 52, textAlign: "right", flex: "0 0 auto", color: valueColor }}
      >
        {pct.toFixed(1)}%
      </span>
    </div>
  );
}

import { useEffect, useRef } from "react";
import type { ResourceMap as ResourceMapData } from "../api/types";
import { ACCENT, magma } from "./charts/colors";
import { Panel } from "./Panel";

interface ResourceMapProps {
  map: ResourceMapData;
}

// Inset reserved on the right for the vertical colorbar (device px scaled later).
const BAR_W = 14;
const BAR_GAP = 34; // room for colorbar + its labels
const PAD = { top: 10, right: BAR_W + BAR_GAP, bottom: 10, left: 10 };

interface Extent {
  min: number;
  max: number;
  span: number;
}

function extent(values: number[]): Extent {
  let min = Infinity;
  let max = -Infinity;
  for (const v of values) {
    if (v < min) min = v;
    if (v > max) max = v;
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    min = 0;
    max = 1;
  }
  const span = max - min || 1;
  return { min, max, span };
}

function maxOfGrid(grid: number[][]): number {
  let m = 0;
  for (const row of grid) {
    for (const v of row) {
      if (v > m) m = v;
    }
  }
  return m || 1;
}

/** Canvas magma heatmap of resource power with well / demand / recommended overlays. */
export function ResourceMap({ map }: ResourceMapProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    if (!canvas || !wrap) return;

    const draw = () => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const cssW = Math.max(wrap.clientWidth, 200);
      const cssH = 420;
      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);
      canvas.style.width = `${cssW}px`;
      canvas.style.height = `${cssH}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, cssW, cssH);

      const plot = {
        x0: PAD.left,
        y0: PAD.top,
        w: cssW - PAD.left - PAD.right,
        h: cssH - PAD.top - PAD.bottom,
      };

      const ex = extent(map.x);
      const ey = extent(map.y);
      const maxPower = maxOfGrid(map.power);

      // Data RD-metres -> canvas px. North is up, so y is inverted.
      const toX = (dataX: number) => plot.x0 + ((dataX - ex.min) / ex.span) * plot.w;
      const toY = (dataY: number) => plot.y0 + (1 - (dataY - ey.min) / ey.span) * plot.h;

      const rows = map.power.length;
      const cols = rows > 0 ? map.power[0].length : 0;

      // Heatmap cells. Each cell spans one step of the x/y grid; draw slightly
      // oversized to avoid seams from sub-pixel rounding.
      if (rows > 0 && cols > 0) {
        const cw = plot.w / cols;
        const ch = plot.h / rows;
        for (let r = 0; r < rows; r++) {
          // row 0 -> bottom-most y after inversion; rows increase with y (north).
          const cellTopY = plot.y0 + (1 - (r + 1) / rows) * plot.h;
          const power = map.power[r];
          for (let c = 0; c < cols; c++) {
            const v = power[c];
            ctx.fillStyle = magma(v / maxPower);
            ctx.fillRect(
              plot.x0 + c * cw,
              cellTopY,
              Math.ceil(cw) + 1,
              Math.ceil(ch) + 1,
            );
          }
        }
      }

      // Plot frame.
      ctx.strokeStyle = ACCENT.axis;
      ctx.lineWidth = 1;
      ctx.strokeRect(plot.x0 + 0.5, plot.y0 + 0.5, plot.w - 1, plot.h - 1);

      ctx.font = "10px var(--font-mono), ui-monospace, monospace";
      ctx.textBaseline = "middle";

      // Wells.
      for (const well of map.wells) {
        const wx = toX(well.x);
        const wy = toY(well.y);
        const viable = well.p50 > 0;
        ctx.lineWidth = 1.25;
        if (viable) {
          ctx.beginPath();
          ctx.arc(wx, wy, 4, 0, Math.PI * 2);
          ctx.fillStyle = ACCENT.heat;
          ctx.fill();
          ctx.strokeStyle = "#ffffff";
          ctx.stroke();
        } else {
          // Tight well: hollow ring with an X through it.
          ctx.beginPath();
          ctx.arc(wx, wy, 4, 0, Math.PI * 2);
          ctx.strokeStyle = "#ffffff";
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(wx - 3, wy - 3);
          ctx.lineTo(wx + 3, wy + 3);
          ctx.moveTo(wx + 3, wy - 3);
          ctx.lineTo(wx - 3, wy + 3);
          ctx.strokeStyle = ACCENT.bad;
          ctx.stroke();
        }
        ctx.fillStyle = "rgba(230,238,248,0.85)";
        ctx.textAlign = "left";
        ctx.fillText(well.id, wx + 7, wy);
      }

      // Demand point: red diamond.
      {
        const dx = toX(map.demand.x);
        const dy = toY(map.demand.y);
        const s = 6;
        ctx.beginPath();
        ctx.moveTo(dx, dy - s);
        ctx.lineTo(dx + s, dy);
        ctx.lineTo(dx, dy + s);
        ctx.lineTo(dx - s, dy);
        ctx.closePath();
        ctx.fillStyle = ACCENT.bad;
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Recommended point: cyan plus with label.
      {
        const rx = toX(map.recommended.x);
        const ry = toY(map.recommended.y);
        ctx.strokeStyle = ACCENT.coolHi;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(rx - 7, ry);
        ctx.lineTo(rx + 7, ry);
        ctx.moveTo(rx, ry - 7);
        ctx.lineTo(rx, ry + 7);
        ctx.stroke();
        const label = `NEW ${map.recommended.power_mw_p50.toFixed(1)} MW`;
        ctx.font = "10px var(--font-mono), ui-monospace, monospace";
        ctx.fillStyle = ACCENT.coolHi;
        ctx.textAlign = "left";
        ctx.fillText(label, rx + 9, ry - 8);
      }

      // Vertical colorbar on the right.
      const barX = cssW - PAD.right + BAR_GAP - BAR_W;
      const barY = plot.y0;
      const barH = plot.h;
      const steps = 64;
      for (let i = 0; i < steps; i++) {
        // i = 0 at bottom (low) -> top (high).
        const t = i / (steps - 1);
        ctx.fillStyle = magma(t);
        const segH = barH / steps;
        ctx.fillRect(barX, barY + (1 - (i + 1) / steps) * barH, BAR_W, segH + 1);
      }
      ctx.strokeStyle = ACCENT.axis;
      ctx.lineWidth = 1;
      ctx.strokeRect(barX + 0.5, barY + 0.5, BAR_W - 1, barH - 1);

      ctx.fillStyle = ACCENT.text;
      ctx.font = "10px var(--font-mono), ui-monospace, monospace";
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(maxPower.toFixed(1), barX + BAR_W + 4, barY + 8);
      ctx.textBaseline = "alphabetic";
      ctx.fillText("0", barX + BAR_W + 4, barY + barH);
    };

    draw();

    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => draw());
      ro.observe(wrap);
    }
    return () => {
      if (ro) ro.disconnect();
    };
  }, [map]);

  return (
    <Panel label="RESOURCE POWER MAP (P50 MWth)" accent="heat">
      <div ref={wrapRef} style={{ width: "100%" }}>
        <canvas
          ref={canvasRef}
          style={{ display: "block", width: "100%", borderRadius: 2 }}
        />
      </div>
      <div
        className="label mono"
        style={{
          marginTop: 8,
          color: "var(--text-faint)",
          letterSpacing: "0.04em",
          fontSize: 11,
        }}
      >
        <span style={{ color: ACCENT.heat }}>&#9679;</span> viable well&nbsp;&nbsp;
        <span style={{ color: ACCENT.bad }}>&#10005;</span> tight&nbsp;&nbsp;
        <span style={{ color: ACCENT.bad }}>&#9733;</span> demand&nbsp;&nbsp;
        <span style={{ color: ACCENT.coolHi }}>&#10010;</span> recommended
      </div>
    </Panel>
  );
}

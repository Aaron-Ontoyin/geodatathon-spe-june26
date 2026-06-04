import { useRef, useState } from "react";

interface ScrubFieldProps {
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}

const clamp = (n: number, lo: number, hi: number): number => Math.min(Math.max(n, lo), hi);

const decimalsOf = (step: number): number => {
  const s = String(step);
  return s.includes(".") ? s.split(".")[1].length : 0;
};

const snap = (v: number, step: number): number => Number((Math.round(v / step) * step).toFixed(8));

/** A scrubbable + editable numeric field: drag horizontally to adjust (full panel
    sweep ≈ full range), click to type, arrow keys to step. Replaces the slider. */
export function ScrubField({ value, min, max, step, unit, onChange }: ScrubFieldProps) {
  const [editing, setEditing] = useState(false);
  const [scrubbing, setScrubbing] = useState(false);
  const drag = useRef<{ x: number; v: number; moved: boolean } | null>(null);
  const dec = decimalsOf(step);

  if (editing) {
    return (
      <input
        className="scrub-edit"
        type="text"
        inputMode="decimal"
        autoFocus
        defaultValue={value.toFixed(dec)}
        onFocus={(e) => e.currentTarget.select()}
        onBlur={(e) => {
          const n = Number(e.currentTarget.value);
          if (Number.isFinite(n)) onChange(clamp(n, min, max));
          setEditing(false);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") e.currentTarget.blur();
          else if (e.key === "Escape") setEditing(false);
        }}
      />
    );
  }

  return (
    <div
      className={scrubbing ? "scrub scrubbing" : "scrub"}
      role="spinbutton"
      tabIndex={0}
      aria-valuenow={value}
      aria-valuemin={min}
      aria-valuemax={max}
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture(e.pointerId);
        drag.current = { x: e.clientX, v: value, moved: false };
        setScrubbing(true);
      }}
      onPointerMove={(e) => {
        const d = drag.current;
        if (!d) return;
        const dx = e.clientX - d.x;
        if (Math.abs(dx) > 2) d.moved = true;
        onChange(clamp(snap(d.v + (dx / 240) * (max - min), step), min, max));
      }}
      onPointerUp={(e) => {
        const d = drag.current;
        drag.current = null;
        setScrubbing(false);
        if (e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
        if (d && !d.moved) setEditing(true);
      }}
      onKeyDown={(e) => {
        if (e.key === "ArrowUp" || e.key === "ArrowRight") {
          e.preventDefault();
          onChange(clamp(snap(value + step, step), min, max));
        } else if (e.key === "ArrowDown" || e.key === "ArrowLeft") {
          e.preventDefault();
          onChange(clamp(snap(value - step, step), min, max));
        } else if (e.key === "Enter") {
          setEditing(true);
        }
      }}
    >
      <span className="v">{value.toFixed(dec)}</span>
      {unit ? <span className="u">{unit}</span> : null}
    </div>
  );
}

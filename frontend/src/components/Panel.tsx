import type { CSSProperties, ReactNode } from "react";

interface PanelProps {
  label?: string;
  accent?: "heat" | "cool";
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

/** The framed instrument panel used across the dashboard. */
export function Panel({ label, accent, right, children, className, style }: PanelProps) {
  const accentClass = accent ? `accent-${accent}` : "";
  return (
    <section className={`panel ${accentClass} ${className ?? ""}`} style={style}>
      {(label || right) && (
        <header className="panel-head">
          <span className="label">{label}</span>
          {right}
        </header>
      )}
      <div className="panel-body">{children}</div>
    </section>
  );
}

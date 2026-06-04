import { useEffect, useRef, useState } from "react";
import { Panel } from "./Panel";
import type { Headline } from "../api/types";

interface HeadlineStripProps {
  headline: Headline;
  doublets: number;
}

/** Animate a number from 0 to `target` over `duration` ms with an ease-out curve. */
function useCountUp(target: number, duration = 500): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.min((now - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(target * eased);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setValue(target);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return value;
}

interface MetricProps {
  caption: string;
  value: number;
  digits: number;
  unit: string;
  color: string;
  band?: string;
  first?: boolean;
  big?: boolean;
}

function Metric({ caption, value, digits, unit, color, band, first, big }: MetricProps) {
  const animated = useCountUp(value);
  return (
    <div
      className="metric"
      style={{
        flex: "1 1 0",
        minWidth: 0,
        padding: "4px 22px",
        borderLeft: first ? undefined : "1px solid var(--line)",
      }}
    >
      <span className="label">{caption}</span>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginTop: 6 }}>
        <span
          className="metric-value num mono"
          style={{ fontSize: big ? 34 : 26, lineHeight: 1, color }}
        >
          {animated.toFixed(digits)}
        </span>
        <span className="metric-unit mono" style={{ color: "var(--text-dim)" }}>
          {unit}
        </span>
      </div>
      {band && (
        <span className="metric-band mono" style={{ display: "block", marginTop: 6, color: "var(--text-faint)" }}>
          {band}
        </span>
      )}
    </div>
  );
}

/** A row of large count-up metric readouts summarizing the design headline. */
export function HeadlineStrip({ headline, doublets }: HeadlineStripProps) {
  const band = `P10 ${headline.lcoe_p10.toFixed(0)} · P90 ${headline.lcoe_p90.toFixed(0)}`;
  return (
    <Panel accent="heat">
      <div style={{ display: "flex", alignItems: "stretch", flexWrap: "wrap" }}>
        <Metric
          first
          big
          caption="LCoE"
          value={headline.lcoe_p50}
          digits={1}
          unit="€/GJ"
          color="var(--heat-hi)"
          band={band}
        />
        <Metric
          caption="Heating Cap"
          value={headline.heating_capacity_mw}
          digits={1}
          unit="MWth"
          color="var(--text)"
        />
        <Metric
          caption="Geothermal CF"
          value={headline.capacity_factor * 100}
          digits={0}
          unit="%"
          color="var(--cool-hi)"
        />
        <Metric
          caption="Capex"
          value={headline.capex_meur}
          digits={0}
          unit="M€"
          color="var(--text)"
        />
        <Metric
          caption="Wells"
          value={doublets}
          digits={0}
          unit="doublet(s)"
          color="var(--text)"
        />
      </div>
    </Panel>
  );
}

import { useEffect, useRef, useState } from "react";

import type { Headline, Objective } from "../api/types";
import { Panel } from "./Panel";
import { Tooltip } from "./Tooltip";

interface HeadlineStripProps {
  headline: Headline;
  doublets: number;
  /** The objective the displayed result was optimised for (optimize mode), if any. */
  objective?: Objective | null;
}

/** Animate a number from 0 to `target` over `duration` ms with an ease-out curve. */
function useCountUp(target: number, duration = 500): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(target * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
      else setValue(target);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return value;
}

const clamp01 = (n: number): number => Math.min(Math.max(n, 0), 1);

interface StatProps {
  caption: string;
  value: number;
  digits: number;
  unit: string;
  accent?: boolean;
  flagged?: boolean;
}

function Stat({ caption, value, digits, unit, accent, flagged }: StatProps) {
  const animated = useCountUp(value);
  return (
    <div className="hl-stat">
      <span className="label">
        {caption}
        {flagged && (
          <Tooltip label="The metric you optimised for" side="top">
            <span className="hl-obj" tabIndex={0}>
              {" "}
              ◆
            </span>
          </Tooltip>
        )}
      </span>
      <div className="hl-stat-v">
        <span className="num mono" style={accent ? { color: "var(--cool-hi)" } : undefined}>
          {animated.toFixed(digits)}
        </span>
        <span className="hl-stat-u mono">{unit}</span>
      </div>
    </div>
  );
}

/** Headline scorecard: LCoE as the hero (with its P10–P90 uncertainty band), then the
    supporting metrics; the optimised objective is flagged in the supporting row. */
export function HeadlineStrip({ headline, doublets, objective }: HeadlineStripProps) {
  const lcoe = useCountUp(headline.lcoe_p50);
  const span = Math.max(headline.lcoe_p90 - headline.lcoe_p10, 1e-6);
  const p50pos = clamp01((headline.lcoe_p50 - headline.lcoe_p10) / span);

  return (
    <Panel>
      <div className="headline">
        <div className="hl-hero">
          <span className="label">Levelised cost · P50</span>
          <div className="hl-big">
            <span className="hl-num num mono">{lcoe.toFixed(1)}</span>
            <span className="hl-unit mono">€/GJ</span>
          </div>
          <div className="hl-band">
            <div className="hl-track">
              <span className="hl-p50" style={{ left: `${p50pos * 100}%` }} />
            </div>
            <div className="hl-band-x mono">
              <span>P10 {headline.lcoe_p10.toFixed(1)}</span>
              <span>P90 {headline.lcoe_p90.toFixed(1)}</span>
            </div>
          </div>
        </div>

        <div className="hl-stats">
          <Stat
            caption="Heating cap"
            value={headline.heating_capacity_mw}
            digits={1}
            unit="MWth"
            flagged={objective === "max_capacity"}
          />
          <Stat caption="Geothermal CF" value={headline.capacity_factor * 100} digits={0} unit="%" accent />
          <Stat
            caption="CAPEX"
            value={headline.capex_meur}
            digits={0}
            unit="M€"
            flagged={objective === "min_capex"}
          />
          <Stat
            caption="Wells"
            value={doublets}
            digits={0}
            unit={doublets === 1 ? "doublet" : "doublets"}
          />
        </div>
      </div>
    </Panel>
  );
}

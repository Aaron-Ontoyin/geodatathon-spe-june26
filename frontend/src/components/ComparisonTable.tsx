import type { Candidate } from "../api/types";
import { Panel } from "./Panel";

interface ComparisonTableProps {
  candidates: Candidate[];
  bestDoublets: number;
}

/** Design comparison table, one row per candidate, highlighting the best design. */
export function ComparisonTable({ candidates, bestDoublets }: ComparisonTableProps) {
  return (
    <Panel label="DESIGN COMPARISON">
      <table className="tbl">
        <thead>
          <tr>
            <th className="label">DESIGN</th>
            <th className="label num">GEO MW</th>
            <th className="label num">LCoE €/GJ</th>
            <th className="label num">CAPEX M€</th>
            <th className="label num">BACKUP %</th>
            <th className="label">FEASIBLE</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr
              key={c.n_doublets}
              className={c.n_doublets === bestDoublets ? "is-best" : undefined}
            >
              <td className="mono">
                {c.n_doublets} doublet{c.n_doublets === 1 ? "" : "s"}
              </td>
              <td className="mono num">{c.geo_capacity_mw.toFixed(1)}</td>
              <td className="mono num">{c.lcoe_eur_per_gj.toFixed(2)}</td>
              <td className="mono num">{c.capex_meur.toFixed(1)}</td>
              <td className="mono num">{(c.backup_fraction * 100).toFixed(0)}</td>
              <td>
                {c.meets_demand ? (
                  <span className="tag cool">OK</span>
                ) : (
                  <span className="tag">–</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

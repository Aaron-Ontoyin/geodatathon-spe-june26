import type { Assumptions, ConfigResponse, Objective } from "../api/types";

const PRIMARY = [
  "heating_peak_mw",
  "cooling_peak_mw",
  "heat_pump_cop",
  "injection_temp_c",
  "electricity_price_eur_per_mwhe",
  "gas_price_eur_per_mwhth",
  "well_cost_meur",
  "discount_rate",
];

const LABELS: Record<string, string> = {
  heating_peak_mw: "Heating peak (MWth)",
  cooling_peak_mw: "Cooling peak (MWth)",
  heat_pump_cop: "Heat-pump COP",
  injection_temp_c: "Injection temp (°C)",
  electricity_price_eur_per_mwhe: "Electricity (€/MWhe)",
  gas_price_eur_per_mwhth: "Gas (€/MWhth)",
  well_cost_meur: "Well cost (M€)",
  discount_rate: "Discount rate",
};

const pretty = (n: string): string => LABELS[n] ?? n.replace(/_/g, " ");

function bounds(name: string, value: number): [number, number] {
  if (name === "discount_rate") return [0, 0.2];
  if (name.includes("rate") || name.includes("efficiency") || name.includes("round_trip"))
    return [0, 1];
  if (name.endsWith("_cop") && name !== "circulation_pump_cop") return [1, 10];
  return [0, Math.max(value * 3, value + 1)];
}

const OBJECTIVES: { id: Objective; label: string }[] = [
  { id: "min_lcoe", label: "MIN LCoE" },
  { id: "min_capex", label: "MIN CAPEX" },
  { id: "max_capacity", label: "MAX CAP" },
];

export interface SearchState {
  ranges: Record<string, [number, number]>;
  constraints: { max_capex_meur?: number; max_lcoe_eur_per_gj?: number };
  objective: Objective;
}

interface InputsPanelProps {
  config: ConfigResponse | null;
  values: Assumptions;
  onChange: (key: string, value: number) => void;
  mode: "single" | "optimize";
  search: SearchState;
  onSearch: (next: SearchState) => void;
  onExport: () => void;
}

export function InputsPanel({
  config,
  values,
  onChange,
  mode,
  search,
  onSearch,
  onExport,
}: InputsPanelProps) {
  if (!config) return <div className="label">loading config…</div>;

  const advanced = config.fields.map((f) => f.name).filter((n) => !PRIMARY.includes(n));

  const toggleRange = (name: string) => {
    const next = { ...search.ranges };
    if (next[name]) delete next[name];
    else {
      const v = values[name] ?? 0;
      next[name] = [Number((v * 0.7).toFixed(3)), Number((v * 1.3).toFixed(3))];
    }
    onSearch({ ...search, ranges: next });
  };

  const setBound = (name: string, idx: 0 | 1, v: number) => {
    const pair: [number, number] = [...(search.ranges[name] ?? [0, 0])];
    pair[idx] = v;
    onSearch({ ...search, ranges: { ...search.ranges, [name]: pair } });
  };

  return (
    <div>
      {PRIMARY.map((name) => {
        const v = values[name] ?? 0;
        const [lo, hi] = bounds(name, config.defaults[name] ?? v);
        const searched = name in search.ranges;
        return (
          <div className="field" key={name}>
            <div className="field-row">
              <span className="label">{pretty(name)}</span>
              <span className="field-val">
                {v}
                {mode === "optimize" && (
                  <button
                    className="tag"
                    style={{ marginLeft: 8, color: searched ? "var(--cool-hi)" : undefined }}
                    onClick={() => toggleRange(name)}
                    title="search this as a range"
                  >
                    {searched ? "↔ RANGE" : "FIX"}
                  </button>
                )}
              </span>
            </div>
            {searched ? (
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="number"
                  value={search.ranges[name][0]}
                  onChange={(e) => setBound(name, 0, Number(e.target.value))}
                />
                <input
                  type="number"
                  value={search.ranges[name][1]}
                  onChange={(e) => setBound(name, 1, Number(e.target.value))}
                />
              </div>
            ) : (
              <input
                type="range"
                min={lo}
                max={hi}
                step={(hi - lo) / 200 || 0.01}
                value={v}
                onChange={(e) => onChange(name, Number(e.target.value))}
              />
            )}
          </div>
        );
      })}

      {mode === "optimize" && (
        <>
          <div className="group-title">
            <span className="label">Constraints</span>
          </div>
          <div className="field">
            <div className="field-row">
              <span className="label">Max CAPEX (M€)</span>
            </div>
            <input
              type="number"
              placeholder="none"
              value={search.constraints.max_capex_meur ?? ""}
              onChange={(e) =>
                onSearch({
                  ...search,
                  constraints: {
                    ...search.constraints,
                    max_capex_meur: e.target.value ? Number(e.target.value) : undefined,
                  },
                })
              }
            />
          </div>
          <div className="field">
            <div className="field-row">
              <span className="label">Max LCoE (€/GJ)</span>
            </div>
            <input
              type="number"
              placeholder="none"
              value={search.constraints.max_lcoe_eur_per_gj ?? ""}
              onChange={(e) =>
                onSearch({
                  ...search,
                  constraints: {
                    ...search.constraints,
                    max_lcoe_eur_per_gj: e.target.value ? Number(e.target.value) : undefined,
                  },
                })
              }
            />
          </div>
          <div className="group-title">
            <span className="label">Objective</span>
          </div>
          <div className="seg">
            {OBJECTIVES.map((o) => (
              <button
                key={o.id}
                className={search.objective === o.id ? "active" : ""}
                onClick={() => onSearch({ ...search, objective: o.id })}
              >
                {o.label}
              </button>
            ))}
          </div>
        </>
      )}

      <details style={{ marginTop: "var(--s5)" }}>
        <summary className="label" style={{ cursor: "pointer" }}>
          Advanced parameters
        </summary>
        <div style={{ marginTop: "var(--s3)" }}>
          {advanced.map((name) => (
            <div className="field" key={name}>
              <div className="field-row">
                <span className="label">{pretty(name)}</span>
              </div>
              <input
                type="number"
                value={values[name] ?? 0}
                onChange={(e) => onChange(name, Number(e.target.value))}
              />
            </div>
          ))}
        </div>
      </details>

      <button className="btn" style={{ marginTop: "var(--s4)", width: "100%" }} onClick={onExport}>
        EXPORT inputs.toml
      </button>
    </div>
  );
}

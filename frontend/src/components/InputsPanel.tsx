import { useMemo, useState } from "react";

import type { Assumptions, ConfigResponse, Objective } from "../api/types";
import { DEFAULT_OPEN, FIELD_GROUPS, type FieldDef, type FieldGroup } from "./fieldGroups";
import { ScrubField } from "./ScrubField";
import { Tooltip } from "./Tooltip";

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

const prettify = (name: string): string =>
  name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

interface ParamRowProps {
  field: FieldDef;
  value: number;
  description?: string;
  optimize: boolean;
  range?: [number, number];
  onValue: (v: number) => void;
  onToggleRange: () => void;
  onBound: (idx: 0 | 1, v: number) => void;
}

function ParamRow({
  field,
  value,
  description,
  optimize,
  range,
  onValue,
  onToggleRange,
  onBound,
}: ParamRowProps) {
  const label = description ? (
    <Tooltip label={description} side="right">
      <span className="pk-label has-tip" tabIndex={0}>
        {field.label}
      </span>
    </Tooltip>
  ) : (
    <span className="pk-label">{field.label}</span>
  );

  return (
    <div className="prow">
      <div className="pk">{label}</div>
      <div className="pctl">
        {optimize && range ? (
          <div className="prange">
            <input
              type="number"
              aria-label={`${field.label} minimum`}
              value={range[0]}
              onChange={(e) => onBound(0, Number(e.target.value))}
            />
            <span className="dash">–</span>
            <input
              type="number"
              aria-label={`${field.label} maximum`}
              value={range[1]}
              onChange={(e) => onBound(1, Number(e.target.value))}
            />
          </div>
        ) : (
          <ScrubField
            value={value}
            min={field.min}
            max={field.max}
            step={field.step}
            unit={field.unit}
            onChange={onValue}
          />
        )}
        {optimize && (
          <Tooltip label={range ? "Fix to a single value" : "Search this as a range"}>
            <button
              type="button"
              className={range ? "rng-toggle is-on" : "rng-toggle"}
              onClick={onToggleRange}
            >
              {range ? "↔" : "FIX"}
            </button>
          </Tooltip>
        )}
      </div>
    </div>
  );
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
  const [filter, setFilter] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(
    () => new Set(FIELD_GROUPS.map((g) => g.title).filter((t) => !DEFAULT_OPEN.includes(t))),
  );

  const descOf = useMemo(() => {
    const m: Record<string, string> = {};
    for (const f of config?.fields ?? []) if (f.description) m[f.name] = f.description;
    return m;
  }, [config]);

  // Fold any backend field not covered by FIELD_GROUPS into an "Other" group.
  const groups = useMemo<FieldGroup[]>(() => {
    if (!config) return FIELD_GROUPS;
    const known = new Set(FIELD_GROUPS.flatMap((g) => g.fields.map((f) => f.name)));
    const extra: FieldDef[] = config.fields
      .filter((f) => !known.has(f.name))
      .map((f) => ({
        name: f.name,
        label: prettify(f.name),
        unit: "",
        min: 0,
        max: Math.max((config.defaults[f.name] ?? 1) * 3, 1),
        step: 0.01,
      }));
    return extra.length ? [...FIELD_GROUPS, { title: "Other", fields: extra }] : FIELD_GROUPS;
  }, [config]);

  if (!config) return <div className="params-empty label">loading config…</div>;

  const toggleGroup = (title: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });

  const toggleRange = (name: string) => {
    const next = { ...search.ranges };
    if (next[name]) delete next[name];
    else {
      const v = values[name] ?? config.defaults[name] ?? 0;
      next[name] = [Number((v * 0.7).toFixed(3)), Number((v * 1.3).toFixed(3))];
    }
    onSearch({ ...search, ranges: next });
  };

  const setBound = (name: string, idx: 0 | 1, v: number) => {
    const pair: [number, number] = [...(search.ranges[name] ?? [0, 0])];
    pair[idx] = v;
    onSearch({ ...search, ranges: { ...search.ranges, [name]: pair } });
  };

  const q = filter.trim().toLowerCase();
  const matches = (f: FieldDef) => !q || f.label.toLowerCase().includes(q) || f.name.includes(q);
  const total = groups.reduce((n, g) => n + g.fields.length, 0);
  const shown = groups.reduce((n, g) => n + g.fields.filter(matches).length, 0);

  return (
    <div className="params">
      <div className="params-head">
        <span className="label">Parameters · {q ? `${shown}/${total}` : total}</span>
        <input
          className="param-filter"
          type="search"
          placeholder="filter parameters…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      {groups.map((g) => {
        const fields = g.fields.filter(matches);
        if (q && fields.length === 0) return null;
        const open = q ? true : !collapsed.has(g.title);
        return (
          <section className={open ? "pgroup" : "pgroup collapsed"} key={g.title}>
            <button
              type="button"
              className="pgroup-head"
              onClick={() => !q && toggleGroup(g.title)}
              aria-expanded={open}
            >
              <span className="chev" aria-hidden="true">
                ▾
              </span>
              <span className="t">{g.title}</span>
              <span className="n">{g.fields.length}</span>
            </button>
            <div className="pgroup-body">
              {fields.map((f) => (
                <ParamRow
                  key={f.name}
                  field={f}
                  value={values[f.name] ?? config.defaults[f.name] ?? 0}
                  description={descOf[f.name]}
                  optimize={mode === "optimize"}
                  range={search.ranges[f.name]}
                  onValue={(v) => onChange(f.name, v)}
                  onToggleRange={() => toggleRange(f.name)}
                  onBound={(idx, v) => setBound(f.name, idx, v)}
                />
              ))}
            </div>
          </section>
        );
      })}

      {mode === "optimize" && (
        <div className="params-opt">
          <div className="group-title">
            <span className="label">Constraints</span>
          </div>
          <div className="field">
            <div className="field-row">
              <span className="label">Max CAPEX</span>
              <span className="field-val">M€</span>
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
              <span className="label">Max LCoE</span>
              <span className="field-val">€/GJ</span>
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
                type="button"
                className={search.objective === o.id ? "active" : ""}
                onClick={() => onSearch({ ...search, objective: o.id })}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="params-foot">
        <button className="btn" type="button" style={{ width: "100%" }} onClick={onExport}>
          EXPORT inputs.toml
        </button>
      </div>
    </div>
  );
}

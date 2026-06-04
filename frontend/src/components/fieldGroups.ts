// Presentation metadata for the parameters panel: how the Assumptions fields are
// grouped, labelled, and what scrub range/step each uses. Field names must match
// the backend Assumptions model (the panel also folds in any unknown backend field
// under an "Other" group, so this staying in sync is not load-bearing).

export interface FieldDef {
  name: string;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
}

export interface FieldGroup {
  title: string;
  fields: FieldDef[];
}

export const FIELD_GROUPS: FieldGroup[] = [
  {
    title: "Demand & Loads",
    fields: [
      { name: "heating_peak_mw", label: "Heating peak", unit: "MWth", min: 5, max: 25, step: 0.1 },
      { name: "cooling_peak_mw", label: "Cooling peak", unit: "MWth", min: 0, max: 20, step: 0.1 },
      { name: "free_cooling_mw", label: "Free cooling", unit: "MWth", min: 0, max: 5, step: 0.1 },
    ],
  },
  {
    title: "Subsurface & Wells",
    fields: [
      { name: "injection_temp_c", label: "Injection temp", unit: "°C", min: 10, max: 60, step: 1 },
      { name: "min_well_spacing_km", label: "Well spacing", unit: "km", min: 0.5, max: 3, step: 0.1 },
      { name: "demand_distance_weight_mw_per_km", label: "Distance penalty", unit: "MW/km", min: 0, max: 1, step: 0.01 },
      { name: "well_cost_meur", label: "Well cost", unit: "M€", min: 1, max: 8, step: 0.01 },
      { name: "pump_cost_meur", label: "Pump cost", unit: "M€", min: 0, max: 1.5, step: 0.01 },
    ],
  },
  {
    title: "Plant & Equipment",
    fields: [
      { name: "heat_pump_cop", label: "Heat-pump COP", unit: "", min: 2, max: 8, step: 0.1 },
      { name: "absorption_cop", label: "Absorption COP", unit: "", min: 0.3, max: 1.2, step: 0.01 },
      { name: "compression_cop", label: "Compression COP", unit: "", min: 2, max: 8, step: 0.1 },
      { name: "circulation_pump_cop", label: "Circulation COP", unit: "", min: 5, max: 60, step: 1 },
      { name: "ates_round_trip", label: "HT-ATES round-trip", unit: "", min: 0.4, max: 0.95, step: 0.01 },
      { name: "backup_boiler_efficiency", label: "Backup boiler eff.", unit: "", min: 0.7, max: 1, step: 0.01 },
      { name: "heat_plant_keur_per_mwth", label: "Heat plant capex", unit: "k€/MWth", min: 50, max: 400, step: 5 },
      { name: "heat_pump_keur_per_mwth", label: "Heat-pump capex", unit: "k€/MWth", min: 400, max: 1000, step: 5 },
      { name: "absorption_keur_per_mwth", label: "Absorption capex", unit: "k€/MWth", min: 200, max: 700, step: 5 },
      { name: "compression_keur_per_mwth", label: "Compression capex", unit: "k€/MWth", min: 50, max: 400, step: 5 },
      { name: "backup_keur_per_mwth", label: "Backup capex", unit: "k€/MWth", min: 20, max: 200, step: 5 },
      { name: "ates_meur", label: "HT-ATES capex", unit: "M€", min: 0.5, max: 6, step: 0.1 },
    ],
  },
  {
    title: "Energy Prices & O&M",
    fields: [
      { name: "electricity_price_eur_per_mwhe", label: "Electricity", unit: "€/MWhe", min: 50, max: 300, step: 1 },
      { name: "gas_price_eur_per_mwhth", label: "Gas", unit: "€/MWhth", min: 10, max: 80, step: 1 },
      { name: "variable_om_eur_per_mwhth", label: "Variable O&M", unit: "€/MWhth", min: 0, max: 20, step: 0.1 },
    ],
  },
  {
    title: "Economics",
    fields: [
      { name: "discount_rate", label: "Discount rate", unit: "", min: 0, max: 0.2, step: 0.001 },
      { name: "economic_lifetime_years", label: "Lifetime", unit: "yr", min: 5, max: 40, step: 1 },
      { name: "fixed_om_rate", label: "Fixed O&M rate", unit: "", min: 0, max: 0.1, step: 0.001 },
      { name: "max_backup_fraction", label: "Max backup", unit: "", min: 0, max: 0.5, step: 0.01 },
    ],
  },
];

/** Groups expanded by default; the rest start collapsed. */
export const DEFAULT_OPEN: readonly string[] = ["Demand & Loads", "Energy Prices & O&M", "Economics"];

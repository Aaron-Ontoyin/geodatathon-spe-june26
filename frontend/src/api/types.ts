// Types mirroring the FastAPI backend payloads (geothermal/api).

export type Assumptions = Record<string, number>;

export interface FieldMeta {
  name: string;
  default: number;
  description: string | null;
}

export interface ConfigResponse {
  defaults: Assumptions;
  fields: FieldMeta[];
}

export type Objective = "min_lcoe" | "min_capex" | "max_capacity";

export interface InputSpec {
  assumptions?: Assumptions;
  search?: {
    ranges?: Record<string, [number, number]>;
    constraints?: Record<string, number>;
    objective?: Objective;
  };
}

export interface Candidate {
  n_doublets: number;
  geo_capacity_mw: number;
  heating_capacity_mw: number;
  lcoe_eur_per_gj: number;
  lcoe_heat_only_eur_per_gj: number;
  capex_meur: number;
  backup_fraction: number;
  meets_demand: boolean;
  capex_breakdown: Record<string, number>;
  assumptions: Assumptions;
}

export interface Headline {
  lcoe_p10: number;
  lcoe_p50: number;
  lcoe_p90: number;
  n_doublets: number;
  heating_capacity_mw: number;
  capex_meur: number;
  capacity_factor: number;
}

export interface DesignSeries {
  months: number[];
  heating_mw: number[];
  cooling_mw: number[];
  geo_heat_mw: number[];
  abs_cool_mw: number[];
  backup_mw: number[];
  capacity_factor: number;
  capacity_factor_heating_only: number;
  heat_gwh: number;
  cool_gwh: number;
}

export interface Well {
  id: string;
  x: number;
  y: number;
  p50: number;
}

export interface Recommended {
  x: number;
  y: number;
  transmissivity_dm: number;
  temperature_c: number;
  power_mw_p50: number;
  distance_to_usp_km: number;
  distance_to_blt_km: number;
}

export interface ResourceMap {
  x: number[];
  y: number[];
  power: number[][];
  wells: Well[];
  demand: { x: number; y: number };
  recommended: Recommended;
}

export interface Percentile {
  well: string;
  p90: number;
  p50: number;
  p10: number;
}

export interface MonteCarlo {
  p10: number;
  p50: number;
  p90: number;
  mean: number;
  hist_counts: number[];
  hist_edges: number[];
}

export interface TornadoRow {
  field: string;
  low: number;
  high: number;
  swing: number;
}

export interface Dashboard {
  assumptions: Assumptions;
  best: Candidate;
  comparison: Candidate[];
  headline: Headline;
  design: DesignSeries;
  resource_map: ResourceMap;
  percentiles: Percentile[];
  monte_carlo: MonteCarlo;
  tornado: TornadoRow[];
}

export interface ProgressEvent {
  stage: string;
  done: number;
  total: number;
  fraction: number;
  message: string;
}

export interface SearchResultPayload {
  best: Candidate | null;
  feasible: Candidate[];
  n_evaluated: number;
  objective: Objective;
}

export interface WorkflowStep {
  name: string;
  action: string;
  decision: string;
  metrics: Record<string, number>;
}

export interface WorkflowPayload {
  steps: WorkflowStep[];
  lcoe_eur_per_gj: number;
  n_doublets: number;
}

export interface ChatRequest {
  question: string;
  history: [string, string][];
  context: string;
  api_key?: string | null;
}
